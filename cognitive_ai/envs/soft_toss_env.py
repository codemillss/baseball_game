import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np

class SoftTossEnv(gym.Env):
    """
    Phase 1-B: Soft-Toss Batting Environment (25~30 km/h)
    - 6m 전방에서 포물선을 그리며 시속 ~28km/h로 날아오는 소프트토스 배팅볼
    - Observation (6차원): [ball_x, ball_y, ball_z, ball_vx, ball_vy, ball_vz]
    - Action (2차원): [swing_trigger, target_z_delta]
      * swing_trigger > 0.0: 스윙 시작 트리거 (타이밍 판단)
      * target_z_delta [-1, 1]: 타격 높이 조절 (0.65m ~ 0.95m 대응)
    """
    def __init__(self, xml_path="shared_assets/h1_baseball.xml", render_mode=None):
        super().__init__()
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        self.data = mujoco.MjData(self.model)
        
        # Observation (8차원):
        # [ball_x, ball_y, ball_z, ball_vx, ball_vy, ball_vz, time_to_plate, predicted_z_at_plate]
        self.observation_space = spaces.Box(low=-50.0, high=50.0, shape=(8,), dtype=np.float32)
        
        # Action: [swing_trigger, target_z_delta]
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
        
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        
        # Humanoid joints to control
        self.joint_names = [
            "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
            "left_hip_roll", "left_hip_pitch", "left_knee", "right_hip_roll", "right_hip_pitch", "right_knee"
        ]
        self.qpos_adrs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.joint_names]
        
        # Base Keyframes [torso, rs_p, rs_r, rs_y, r_elbow, l_hr, l_hp, l_k, r_hr, r_hp, r_k]
        self.base_keyframes = np.array([
            [-0.5, -1.0, 0.0, 0.5, 1.5,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stance
            [-1.0, -1.2, 0.0, 0.8, 2.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Load
            [0.0, -0.5, 0.0, 0.0, 1.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stride
            [1.5, 0.5, 0.0, -0.5, 0.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Contact
            [2.0, 1.0, 0.0, -1.0, 1.5,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8]  # Follow-through
        ])
        
        self.render_mode = render_mode
        if render_mode == "human":
            from mujoco import viewer
            self.viewer = viewer.launch_passive(self.model, self.data)
        else:
            self.viewer = None
            
        self.frame_skip = 4
        self.max_steps = 45
        self.current_step = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        self.swing_active = False
        self.swing_progress = 0.0
        self.swing_duration_frames = 24
        self.has_contacted = False
        self.trigger_ball_y = -999.0
        self.current_keyframes = self.base_keyframes.copy()
        self.current_step = 0
        self.min_dist = 999.0
        
        # Standard baseball mass
        self.model.body_mass[self.ball_body_id] = 0.145
        
        # Soft-toss launch from 4.0m away (28.8 km/h)
        vy = np.random.uniform(-8.2, -7.8)
        # Vertical velocity tuned so ball strictly arrives in strike zone (0.68m ~ 0.95m) at home plate
        vz = np.random.uniform(1.55, 2.05)
        vx = np.random.uniform(-0.04, 0.04)
        
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 4.0, 1.0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
        
        self._update_swing_kinematics(0.0)
        mujoco.mj_forward(self.model, self.data)
        
        return self._get_obs(), {}

    def step(self, action):
        swing_trigger = float(action[0])
        target_z_delta = float(action[1])
        
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        
        # Start swing if triggered and not active
        if not self.swing_active and swing_trigger > 0.0:
            self.swing_active = True
            self.trigger_ball_y = float(ball_pos[1])
            pitch_adj = -0.80 - target_z_delta * 0.55
            self.current_keyframes = self.base_keyframes.copy()
            self.current_keyframes[3, 1] += pitch_adj # Contact shoulder pitch
            self.current_keyframes[4, 1] += pitch_adj # Follow-through shoulder pitch
            
        reward = 0.0
        
        for _ in range(self.frame_skip):
            if self.swing_active and self.swing_progress < 1.0:
                self._update_swing_kinematics(self.swing_progress)
                self.swing_progress += 1.0 / self.swing_duration_frames
                
            mujoco.mj_step(self.model, self.data)
            
            # Track closest distance
            bat_pos = self.data.geom_xpos[self.bat_geom_id]
            ball_pos = self.data.geom_xpos[self.ball_geom_id]
            dist = np.linalg.norm(bat_pos - ball_pos)
            self.min_dist = min(self.min_dist, dist)
            
            if not self.has_contacted and self._check_contact():
                self.has_contacted = True
                reward += 100.0  # Big bonus for contact!
                
        if self.viewer:
            self.viewer.sync()
            
        self.current_step += 1
        
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        
        terminated = False
        truncated = False
        
        # End episode when ball passes home plate (y < -0.3) or hits ground or swing finishes
        if self.has_contacted or ball_pos[1] < -0.3 or ball_pos[2] < 0.1 or (self.swing_active and self.swing_progress >= 1.0):
            terminated = True
            if self.has_contacted:
                # Big bonus for contact + exit speed
                ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
                exit_speed = np.linalg.norm(ball_vel)
                reward += 150.0 + min(exit_speed * 10.0, 50.0)
            else:
                # Dense quadratic distance penalty
                reward -= 50.0 * (self.min_dist ** 2)
                if self.swing_active:
                    # Timing guidance: optimal trigger is when ball is at Y ~ 1.20m
                    timing_err = abs(self.trigger_ball_y - 1.20)
                    reward -= min(timing_err * 30.0, 30.0)
                else:
                    reward -= 30.0 # Heavy penalty for frozen/no-swing
                    
        if self.current_step >= self.max_steps:
            truncated = True
            
        return self._get_obs(), reward, terminated, truncated, {}

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
        # 8-dim State: [X, Y, Z, Vx, Vy, Vz, time_to_plate, predicted_z_at_plate]
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
        
        # Calculate time remaining to home plate (Y = 0.20m)
        t_remain = float(max(0.0, (ball_pos[1] - 0.20) / max(0.1, -ball_vel[1])))
        # Calculate expected ball Z height when crossing home plate under gravity
        pred_z = float(ball_pos[2] + ball_vel[2] * t_remain - 0.5 * 9.81 * (t_remain ** 2))
        
        features = np.array([t_remain, pred_z], dtype=np.float32)
        return np.concatenate([ball_pos, ball_vel, features]).astype(np.float32)

    def close(self):
        if self.viewer:
            self.viewer.close()
