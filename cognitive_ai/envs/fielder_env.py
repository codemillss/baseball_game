import gymnasium as gym
from gymnasium import spaces
import numpy as np
import mujoco

class FielderEnv(gym.Env):
    def __init__(self):
        super().__init__()
        
        self.model = mujoco.MjModel.from_xml_path("shared_assets/h1_fielder.xml")
        self.data = mujoco.MjData(self.model)
        
        self.frame_skip = 4
        self.dt = self.model.opt.timestep * self.frame_skip
        
        # 12 Actions: 3 base + 9 upper body
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(12,), dtype=np.float32)
        
        # Observation space: 
        # Ball pos (3), Ball vel (3)
        # Base pos (x, y) (2), Base yaw (1), Base vel (x, y, yaw) (3)
        # Upper body pos (9), Upper body vel (9)
        # Total: 3+3 + 2+1+3 + 9+9 = 30
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(30,), dtype=np.float32)
        
        self.upper_joints = [
            "torso",
            "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
            "right_shoulder_pitch", "right_shoulder_roll", "right_shoulder_yaw", "right_elbow"
        ]
        
        self.base_joints = ["base_x", "base_y", "base_yaw"]
        
        # Indices
        self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        
        self.glove_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "glove_site")
        self.ball_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "ball_site")
        
        self.max_steps = 200
        self.current_step = 0
        
    def reset(self, seed=None, options=None):
        if seed is not None:
            np.random.seed(seed)
            
        mujoco.mj_resetData(self.model, self.data)
        
        # Launch ball from origin with random fly ball trajectory
        vx = np.random.uniform(-10.0, 10.0)
        vy = np.random.uniform(15.0, 30.0)
        vz = np.random.uniform(10.0, 25.0)
        
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0.0, 0.0, 1.0]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
        
        # Position fielder roughly where the ball will land
        # Time of flight approx: t = 2 * vz / 9.81
        t_flight = 2 * vz / 9.81
        land_x = vx * t_flight
        land_y = vy * t_flight
        
        # Add some random noise to fielder's starting position so it has to move
        start_x = land_x + np.random.uniform(-5.0, 5.0)
        start_y = land_y + np.random.uniform(-5.0, 5.0)
        
        base_x_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "base_x")
        base_y_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "base_y")
        
        self.data.qpos[self.model.jnt_qposadr[base_x_id]] = start_x
        self.data.qpos[self.model.jnt_qposadr[base_y_id]] = start_y
        
        mujoco.mj_forward(self.model, self.data)
        
        self.current_step = 0
        return self._get_obs(), {}
        
    def _get_obs(self):
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3].copy()
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3].copy()
        
        base_qpos = []
        base_qvel = []
        for j in self.base_joints:
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)
            base_qpos.append(self.data.qpos[self.model.jnt_qposadr[jid]])
            base_qvel.append(self.data.qvel[self.model.jnt_dofadr[jid]])
            
        up_qpos = []
        up_qvel = []
        for j in self.upper_joints:
            jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)
            up_qpos.append(self.data.qpos[self.model.jnt_qposadr[jid]])
            up_qvel.append(self.data.qvel[self.model.jnt_dofadr[jid]])
            
        return np.concatenate([
            ball_pos, ball_vel,
            base_qpos, base_qvel,
            up_qpos, up_qvel
        ]).astype(np.float32)

    def step(self, action):
        # Action mappings to actuators
        # base_x, base_y, base_yaw
        for i, j in enumerate(self.base_joints):
            act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, j)
            self.data.ctrl[act_id] = action[i] * 5.0 # Max speed/force multiplier
            
        # Upper body
        for i, j in enumerate(self.upper_joints):
            act_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, j)
            ctrl_range = self.model.actuator_ctrlrange[act_id]
            # scale -1 to 1 into ctrl_range
            val = ctrl_range[0] + (action[i+3] + 1.0) * 0.5 * (ctrl_range[1] - ctrl_range[0])
            self.data.ctrl[act_id] = val
            
        for _ in range(self.frame_skip):
            mujoco.mj_step(self.model, self.data)
            
        self.current_step += 1
        
        obs = self._get_obs()
        
        # Calculate distance between glove and ball
        glove_pos = self.data.site_xpos[self.glove_site_id]
        ball_pos = self.data.site_xpos[self.ball_site_id]
        dist = np.linalg.norm(glove_pos - ball_pos)
        
        reward = -dist * 0.1 # Penalty for being far
        
        terminated = False
        truncated = False
        info = {"dist": dist}
        
        if dist < 0.25:
            reward += 1000.0
            terminated = True
            info["catch"] = True
            
        elif ball_pos[2] < 0.2:
            # Ball hit the ground
            reward -= 50.0
            terminated = True
            info["catch"] = False
            
        if self.current_step >= self.max_steps:
            truncated = True
            
        return obs, reward, terminated, truncated, info

