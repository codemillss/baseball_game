import gymnasium as gym
import mujoco
import numpy as np
import os

class RunnerEnv(gym.Env):
    def __init__(self, render_mode=None):
        self.model = mujoco.MjModel.from_xml_path("shared_assets/h1_runner.xml")
        self.data = mujoco.MjData(self.model)
        self.render_mode = render_mode
        
        # Action: runner_x, runner_y, runner_yaw (3)
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
        
        # Obs: base_pos(3), base_vel(3), relative_target(2) -> 8
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(8,), dtype=np.float32)
        
        self.actuator_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in [
            "runner_x", "runner_y", "runner_yaw"
        ]]
        
        # 1st base
        self.start_pos = np.array([19.4, 19.4])
        # 2nd base
        self.target_pos = np.array([0.0, 38.8])
        
        self.max_steps = 300

    def _get_obs(self):
        base_pos = self.data.qpos[:3]
        base_vel = self.data.qvel[:3]
        
        curr_xy = base_pos[:2]
        rel_target = self.target_pos - curr_xy
        
        return np.concatenate([
            base_pos, base_vel, rel_target
        ]).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        self.current_step = 0
        
        # Set pos to 1st base
        self.data.qpos[0] = self.start_pos[0]
        self.data.qpos[1] = self.start_pos[1]
        self.data.qpos[2] = 2.35 # yaw pointing to 2nd base approx (3*pi/4)
        
        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(), {}

    def step(self, action):
        for i, act_id in enumerate(self.actuator_ids):
            if act_id != -1:
                self.data.ctrl[act_id] = action[i]
                
        for _ in range(10): # 10 sub-steps
            mujoco.mj_step(self.model, self.data)
            
        self.current_step += 1
        
        curr_xy = self.data.qpos[:2]
        dist = np.linalg.norm(self.target_pos - curr_xy)
        
        # Reward for moving closer
        reward = -dist * 0.05
        
        # Speed reward
        vel = self.data.qvel[:2]
        speed_towards = np.dot(vel, (self.target_pos - curr_xy) / max(dist, 1e-4))
        reward += speed_towards * 0.1
        
        terminated = False
        if dist < 1.0:
            reward += 1000.0
            terminated = True
            
        truncated = self.current_step >= self.max_steps
        info = {"dist": dist}
        
        return self._get_obs(), float(reward), terminated, truncated, info
