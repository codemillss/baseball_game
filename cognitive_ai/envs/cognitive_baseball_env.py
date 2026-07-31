import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np
import cv2

class CognitiveBaseballEnv(gym.Env):
    """
    Macro-Action Based Cognitive Baseball Environment (Humanoid Version).
    """
    def __init__(self, xml_path="shared_assets/h1_baseball.xml", render_mode=None):
        super().__init__()
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        
        self.renderer = mujoco.Renderer(self.model, height=64, width=64)
        
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=255, shape=(64, 64, 3), dtype=np.uint8)
        
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        
        # Humanoid joints to control kinematically (Upper body + Legs for wide stance)
        self.joint_names = [
            "root_y", "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
            "left_hip_roll", "left_hip_pitch", "left_knee", "right_hip_roll", "right_hip_pitch", "right_knee"
        ]
        self.qpos_adrs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.joint_names]
        
        # Humanoid Keyframes [root_y, torso, rs_p, rs_r, rs_y, r_elbow, l_hr, l_hp, l_k, r_hr, r_hp, r_k]
        # Legs are kept at a constant wide stance: roll(0.3, -0.3), pitch(-0.4, -0.4), knee(0.8, 0.8)
        self.base_keyframes = np.array([
            [0.0, -0.5, -1.0, 0.0, 0.5, 1.5,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stance
            [0.0, -1.0, -1.2, 0.0, 0.8, 2.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Load
            [0.0, 0.0, -0.5, 0.0, 0.0, 1.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stride (Hip turn only)
            [0.0, 1.5, 0.5, 0.0, -0.5, 0.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Contact
            [0.0, 2.0, 1.0, 0.0, -1.0, 1.5,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8]  # Follow-through
        ])
        
        self.render_mode = render_mode
        if render_mode == "human":
            from mujoco import viewer
            self.viewer = viewer.launch_passive(self.model, self.data)
        else:
            self.viewer = None
            
        self.frame_skip = 4
        
        # Aerodynamics
        self.mass = 0.145
        self.area = 0.00426
        self.rho = 1.225
        self.Cd = 0.3
        self.Cl = 0.15

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        self.swing_active = False
        self.swing_progress = 0.0
        self.swing_duration_frames = 20
        self.has_contacted = False
        self.current_keyframes = self.base_keyframes.copy()
        
        # Force initial stance
        self._update_swing_kinematics(0.0)
        
        pitch_type = np.random.choice(["fastball", "curveball"])
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [np.random.uniform(-0.1, 0.1), 15.0, 1.6]
        
        if pitch_type == "fastball":
            self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [np.random.uniform(-1, 1), -40.0, -1.0]
            self.ball_spin = np.array([0.0, 0.0, 0.0])
        else:
            self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [np.random.uniform(-1, 1), -30.0, 1.0]
            self.ball_spin = np.array([-50.0, 0.0, 30.0])
            
        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(), {}

    def step(self, action):
        swing_trigger = action[0]
        target_z_delta = action[1]
        swing_speed = action[2]
        
        if not self.swing_active and swing_trigger > 0.0:
            self.swing_active = True
            self.swing_duration_frames = int(np.interp(swing_speed, [-1, 1], [30, 10]))
            
            # Adjust spine pitch or arm to hit higher/lower
            # Since we didn't expose spine_pitch, let's adjust r_shoulder_y (up/down)
            pitch_adj = -target_z_delta * 0.5 
            self.current_keyframes = self.base_keyframes.copy()
            self.current_keyframes[3, 3] += pitch_adj # shoulder_y at contact
            
        reward = 0.0
        
        for _ in range(self.frame_skip):
            self._apply_aerodynamics()
            
            if self.swing_active and self.swing_progress < 1.0:
                self._update_swing_kinematics(self.swing_progress)
                self.swing_progress += 1.0 / self.swing_duration_frames
                
            mujoco.mj_step(self.model, self.data)
            
            if not self.has_contacted:
                if self._check_contact():
                    self.has_contacted = True
                    reward += 10.0
                    
        if self.viewer:
            self.viewer.sync()
            
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        terminated = False
        if ball_pos[1] < -2.0 or ball_pos[2] < 0.1:
            terminated = True
            if not self.has_contacted:
                if abs(ball_pos[0]) < 0.3 and 0.5 < ball_pos[2] < 1.2:
                    reward -= 1.0
                else:
                    reward += 0.5
                    
        return self._get_obs(), reward, terminated, False, {}

    def _apply_aerodynamics(self):
        vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        speed = np.linalg.norm(vel)
        if speed < 0.1: return
        f_drag = -0.5 * self.rho * self.area * self.Cd * speed * vel
        v_hat = vel / speed
        f_magnus = 0.5 * self.rho * self.area * self.Cl * speed * np.cross(self.ball_spin, v_hat)
        self.data.xfrc_applied[self.ball_body_id][:3] = f_drag + f_magnus

    def _update_swing_kinematics(self, progress):
        num_kfs = len(self.current_keyframes)
        scaled = progress * (num_kfs - 1)
        idx1 = int(np.floor(scaled))
        idx2 = min(idx1 + 1, num_kfs - 1)
        t = scaled - idx1
        
        current_angles = (1-t)*self.current_keyframes[idx1] + t*self.current_keyframes[idx2]
        
        for i, adr in enumerate(self.qpos_adrs):
            self.data.qpos[adr] = current_angles[i]
            jnt_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, self.joint_names[i])
            vel_adr = self.model.jnt_dofadr[jnt_id]
            self.data.qvel[vel_adr] = 0.0

    def _check_contact(self):
        for i in range(self.data.ncon):
            contact = self.data.contact[i]
            if (contact.geom1 == self.bat_geom_id and contact.geom2 == self.ball_geom_id) or \
               (contact.geom2 == self.bat_geom_id and contact.geom1 == self.ball_geom_id):
                return True
        return False

    def _get_obs(self):
        self.renderer.update_scene(self.data, camera="batter_cam")
        return self.renderer.render()
