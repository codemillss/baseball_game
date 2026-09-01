import gymnasium as gym
from gymnasium import spaces
import mujoco
import numpy as np

class TeeBallEnv(gym.Env):
    """
    Phase 1-A: Tee-ball Environment (State-based)
    공은 특정 위치(가상의 티대 위)에 정지해 있으며, 픽셀 대신 공의 절대 좌표(X,Y,Z)를 Observation으로 받습니다.
    에이전트는 [스윙_트리거, 타격_높이_조절] 액션을 통해 공을 맞추는 법을 학습합니다.
    """
    def __init__(self, xml_path="shared_assets/h1_baseball.xml", render_mode=None):
        super().__init__()
        self.model = mujoco.MjModel.from_xml_path(xml_path)
        
        self.ball_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "baseball")
        self.data = mujoco.MjData(self.model)
        
        # Observation: [ball_x, ball_y, ball_z]
        self.observation_space = spaces.Box(low=-10.0, high=10.0, shape=(3,), dtype=np.float32)
        
        # Action: [target_z_delta]
        # Controls the vertical bat height adjustment to match the ball height
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(1,), dtype=np.float32)
        
        self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.bat_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "bat_barrel")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        
        # Humanoid joints to control kinematically (Upper body + Legs for wide stance)
        self.joint_names = [
            "torso", "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow",
            "left_hip_roll", "left_hip_pitch", "left_knee", "right_hip_roll", "right_hip_pitch", "right_knee"
        ]
        self.qpos_adrs = [self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in self.joint_names]
        
        # Base Keyframes [torso, rs_p, rs_r, rs_y, r_elbow, l_hr, l_hp, l_k, r_hr, r_hp, r_k]
        self.base_keyframes = np.array([
            [-0.5, -1.0, 0.0, 0.5, 1.5,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stance
            [-1.0, -1.2, 0.0, 0.8, 2.0,   0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Load
            [0.0, -0.5, 0.0, 0.0, 1.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Stride (Hip turn only)
            [1.5, 0.5, 0.0, -0.5, 0.0,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8], # Contact
            [2.0, 1.0, 0.0, -1.0, 1.5,    0.3, -0.4, 0.8, -0.3, -0.4, 0.8]  # Follow-through
        ])
        
        self.render_mode = render_mode
        if render_mode == "human":
            from mujoco import viewer
            self.viewer = viewer.launch_passive(self.model, self.data)
        else:
            self.viewer = None
            
        self.frame_skip = 2
        self.max_steps = 40
        self.current_step = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        self.swing_active = True
        self.swing_progress = 0.0
        self.swing_duration_frames = 25
        self.has_contacted = False
        self.current_keyframes = self.base_keyframes.copy()
        self.current_step = 0
        self.min_dist = 999.0
        
        # Place ball randomly on the tee (varying height Z between 0.65m and 0.95m)
        ball_z = np.random.uniform(0.65, 0.95)
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 0.4, ball_z]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0.0, 0.0, 0.0]
        
        # Counteract gravity for the ball (Tee-ball effect)
        self.model.body_mass[self.ball_body_id] = 1e-6 
        
        self._update_swing_kinematics(0.0)
        mujoco.mj_forward(self.model, self.data)
        
        return self._get_obs(), {}

    def step(self, action):
        target_z_delta = float(action[0])
        
        # Linear kinematic mapping for full strike zone reachability (0.65m ~ 0.95m)
        # action = -1.0 (low ball) -> pitch_adj = -0.25
        # action = 0.0  (mid ball) -> pitch_adj = -0.80
        # action = +1.0 (high ball) -> pitch_adj = -1.35
        pitch_adj = -0.80 - target_z_delta * 0.55
        self.current_keyframes = self.base_keyframes.copy()
        self.current_keyframes[3, 1] += pitch_adj # Contact shoulder pitch
        self.current_keyframes[4, 1] += pitch_adj # Follow-through shoulder pitch
        
        reward = 0.0
        
        for _ in range(self.frame_skip):
            if self.swing_progress < 1.0:
                self._update_swing_kinematics(self.swing_progress)
                self.swing_progress += 1.0 / self.swing_duration_frames
                
            mujoco.mj_step(self.model, self.data)
            
            # Track distance between bat barrel and ball
            bat_pos = self.data.geom_xpos[self.bat_geom_id]
            ball_pos = self.data.geom_xpos[self.ball_geom_id]
            dist = np.linalg.norm(bat_pos - ball_pos)
            self.min_dist = min(self.min_dist, dist)
            
            # Keep ball stationary before hit
            if not self.has_contacted:
                self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [0, 0, 0]
            
            if not self.has_contacted and self._check_contact():
                self.has_contacted = True
                reward += 100.0  # Big reward for hitting the ball!
                
        if self.viewer:
            self.viewer.sync()
            
        self.current_step += 1
        
        terminated = False
        truncated = False
        
        if self.has_contacted or self.swing_progress >= 1.0:
            terminated = True
            if self.has_contacted:
                reward += 100.0  # Big bonus for contact
            else:
                # Dense quadratic penalty: closer = higher reward
                # min_dist ~ 0.05m -> -0.125, min_dist ~ 0.3m -> -4.5
                reward -= 50.0 * (self.min_dist ** 2)
            
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
        # Observation is just the ball's absolute position [X, Y, Z]
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
        return ball_pos.astype(np.float32)

    def close(self):
        if self.viewer:
            self.viewer.close()
