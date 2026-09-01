import gymnasium as gym
import mujoco
import numpy as np
import os

class CatcherEnv(gym.Env):
    def __init__(self, render_mode=None):
        self.model = mujoco.MjModel.from_xml_path("shared_assets/h1_catcher.xml")
        self.data = mujoco.MjData(self.model)
        self.render_mode = render_mode
        
        self.action_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(12,), dtype=np.float32)
        # obs: base_qpos(3), base_qvel(3), arm_qpos(9), arm_qvel(9), ball_pos(3), ball_vel(3) => 30
        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(30,), dtype=np.float32)
        
        self.glove_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "glove_box")
        self.ball_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "ball_geom")
        self.ball_qpos_adr = self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        self.ball_qvel_adr = self.model.jnt_dofadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "ball_joint")]
        
        self.actuator_ids = [mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, name) for name in [
            "catcher_x", "catcher_y", "catcher_yaw",
            "left_shoulder_pitch", "left_shoulder_roll", "left_shoulder_yaw", "left_elbow",
            "torso_yaw", "torso_pitch", "torso_roll", "left_hip_yaw", "left_hip_roll" # fillers
        ]]
        self.max_steps = 150

    def _get_obs(self):
        base_qpos = self.data.qpos[:3]
        base_qvel = self.data.qvel[:3]
        arm_qpos = self.data.qpos[3:12]
        arm_qvel = self.data.qvel[3:12]
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        ball_vel = self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3]
        
        return np.concatenate([
            base_qpos, base_qvel, arm_qpos, arm_qvel, ball_pos, ball_vel
        ]).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        
        self.current_step = 0
        
        # Pitch ball from mound (y=18.4) to home (y=0)
        # Add some random variance to pitch location (Strike zone + wild pitches)
        target_x = np.random.uniform(-0.5, 0.5)
        target_z = np.random.uniform(0.1, 1.5)
        
        vx = target_x / 0.4  # arrives in ~0.4 sec
        vy = -18.4 / 0.4
        vz = (target_z - 1.5 + 0.5 * 9.81 * 0.4**2) / 0.4
        
        self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3] = [0, 18.4, 1.5]
        self.data.qvel[self.ball_qvel_adr:self.ball_qvel_adr+3] = [vx, vy, vz]
        
        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(), {}

    def step(self, action):
        for i, act_id in enumerate(self.actuator_ids[:10]): # Only use first 10 for actual arm/base
            if act_id != -1:
                self.data.ctrl[act_id] = action[i]
                
        for _ in range(10): # 10 sub-steps
            mujoco.mj_step(self.model, self.data)
            
        self.current_step += 1
        
        glove_pos = self.data.geom_xpos[self.glove_geom_id]
        ball_pos = self.data.qpos[self.ball_qpos_adr:self.ball_qpos_adr+3]
        
        dist = np.linalg.norm(glove_pos - ball_pos)
        
        reward = -dist * 0.1
        terminated = False
        caught = False
        
        for i in range(self.data.ncon):
            contact = self.data.contact[i]
            if (contact.geom1 == self.glove_geom_id and contact.geom2 == self.ball_geom_id) or \
               (contact.geom2 == self.glove_geom_id and contact.geom1 == self.ball_geom_id):
                reward += 1000.0
                terminated = True
                caught = True
                break
                
        if ball_pos[1] < -2.0 or ball_pos[2] < 0.1:
            terminated = True
            reward -= 50.0
            
        truncated = self.current_step >= self.max_steps
        info = {"catch": caught, "dist": dist}
        
        return self._get_obs(), float(reward), terminated, truncated, info
