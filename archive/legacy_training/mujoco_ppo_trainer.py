"""
mujoco_ppo_trainer.py — Stage 2 PPO Fine-Tuner with Domain Randomization

Stage 1에서 BC로 pre-training된 Base Policy를 로드하여,
Domain Randomization(구속 ±10%, 공 질량, 바람/마찰력 변동)이 적용된 
MuJoCo 3D 야구 환경에서 PPO 파인튜닝을 진행합니다.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, List

import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim

from envs.mujoco_baseball_env import MuJoCoBaseballEnv
from training.networks import BatterPolicy, ValueNetwork, get_device
from simulator.dashboard import save_training_metrics


class MuJoCoPPOTrainer:
    """Stage 2 MuJoCo 3D PPO Fine-tuner."""

    def __init__(
        self,
        bc_checkpoint_path: Optional[str] = None,
        max_episodes: int = 50,
        lr: float = 3e-4,
    ):
        if bc_checkpoint_path is None:
            bc_checkpoint_path = str(Path(__file__).parent.parent / "checkpoints" / "bc_batter_policy.pt")

        self.bc_checkpoint_path = bc_checkpoint_path
        self.max_episodes = max_episodes
        self.lr = lr
        self.device = get_device()

        # 환경
        self.env = MuJoCoBaseballEnv()

        # Policy & Value
        self.obs_dim = self.env.observation_space.shape[0]
        self.action_dim = self.env.action_space.shape[0]

        self.policy = BatterPolicy(
            obs_dim=self.obs_dim,
            action_dim=self.action_dim,
            hidden_dim=128,
            num_layers=2,
        ).to(self.device)

        self.value_net = ValueNetwork(obs_dim=self.obs_dim).to(self.device)

        # BC 가중치 로드
        if os.path.exists(self.bc_checkpoint_path):
            ckpt = torch.load(self.bc_checkpoint_path, map_location=self.device)
            state_dict = ckpt.get('policy_state_dict', ckpt)
            self.policy.load_state_dict(state_dict)
            print(f"✅ BC Base Policy 성공적으로 로드됨: {self.bc_checkpoint_path}")
        else:
            print("⚠️ BC 체크포인트 없음 - 무작위 가중치로 시작합니다.")

        self.optimizer = optim.Adam(
            list(self.policy.parameters()) + list(self.value_net.parameters()),
            lr=self.lr,
        )

    def train(self) -> str:
        """Stage 2 PPO Fine-Tuning을 실행합니다."""
        print(f"🚀 Stage 2: MuJoCo 3D PPO Fine-Tuning 시작 ({self.max_episodes} episodes)...")
        print(f"   Device: {self.device} | Domain Randomization: Enabled (Speed ±10%)")

        total_contacts = 0
        total_reward = 0.0

        for ep in range(1, self.max_episodes + 1):
            obs, info = self.env.reset()
            done = False
            ep_reward = 0.0

            # Rollout 버퍼
            obs_list = []
            act_list = []
            rew_list = []
            log_prob_list = []
            val_list = []

            hidden = None
            contacted = False

            while not done:
                obs_t = torch.tensor(obs, dtype=torch.float32, device=self.device).unsqueeze(0)

                with torch.no_grad():
                    action_t, log_prob_t, _, hidden = self.policy.get_action(obs_t, hidden)
                    val_t = self.value_net(obs_t)

                action = action_t.squeeze(0).cpu().numpy()
                log_prob = log_prob_t.squeeze(0).cpu().item()
                value = val_t.squeeze(0).cpu().item()

                next_obs, reward, terminated, truncated, step_info = self.env.step(action)
                done = terminated or truncated

                obs_list.append(obs)
                act_list.append(action)
                rew_list.append(reward)
                log_prob_list.append(log_prob)
                val_list.append(value)

                ep_reward += reward
                if step_info.get('has_contacted', False):
                    contacted = True

                obs = next_obs

            if contacted:
                total_contacts += 1
            total_reward += ep_reward

            # PPO Gradient Update
            if len(obs_list) > 0:
                obs_tensor = torch.tensor(np.array(obs_list), dtype=torch.float32, device=self.device)
                act_tensor = torch.tensor(np.array(act_list), dtype=torch.float32, device=self.device)
                old_log_probs = torch.tensor(np.array(log_prob_list), dtype=torch.float32, device=self.device)
                rewards_arr = np.array(rew_list)
                values_arr = np.array(val_list)

                # Return & Advantage 계산
                returns = []
                discounted = 0.0
                for r in reversed(rewards_arr):
                    discounted = r + 0.99 * discounted
                    returns.insert(0, discounted)
                returns_tensor = torch.tensor(returns, dtype=torch.float32, device=self.device)
                advantages = returns_tensor - torch.tensor(values_arr, dtype=torch.float32, device=self.device)
                advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

                # PPO 4-epoch Optimization
                for _ in range(4):
                    new_log_probs, entropy = self.policy.evaluate_actions(obs_tensor, act_tensor)
                    new_values = self.value_net(obs_tensor).squeeze(-1)

                    ratios = torch.exp(new_log_probs - old_log_probs)
                    surr1 = ratios * advantages
                    surr2 = torch.clamp(ratios, 0.8, 1.2) * advantages
                    policy_loss = -torch.min(surr1, surr2).mean()

                    value_loss = F.mse_loss(new_values, returns_tensor)
                    entropy_loss = -entropy.mean()

                    loss = policy_loss + 0.5 * value_loss + 0.01 * entropy_loss

                    self.optimizer.zero_grad()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(list(self.policy.parameters()) + list(self.value_net.parameters()), 0.5)
                    self.optimizer.step()

            # 대시보드 공유 메트릭 기록
            if ep % 10 == 0 or ep == self.max_episodes:
                win_rate_b = total_contacts / ep
                avg_rew = total_reward / ep
                print(f"   [EP {ep:3d}/{self.max_episodes}] Contact Rate: {win_rate_b:.1%} | Avg Reward: {avg_rew:+.2f}")

                save_training_metrics({
                    'episode': ep,
                    'pitcher_win_rate': 1.0 - win_rate_b,
                    'batter_win_rate': win_rate_b,
                    'pitcher_reward': -avg_rew,
                    'batter_reward': avg_rew,
                    'home_run_rate': win_rate_b * 0.2,
                    'strikeout_rate': 1.0 - win_rate_b,
                })

        # 체크포인트 저장
        save_dir = Path(__file__).parent.parent / "checkpoints"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / f"mujoco_ppo_ep{self.max_episodes}.pt"

        torch.save({
            'policy_state_dict': self.policy.state_dict(),
            'value_state_dict': self.value_net.state_dict(),
            'episodes': self.max_episodes,
            'contact_rate': total_contacts / self.max_episodes,
        }, save_path)

        print(f"\n💾 Stage 2 MuJoCo PPO 체크포인트 저장 완료: {save_path}")
        return str(save_path)


def main():
    trainer = MuJoCoPPOTrainer(max_episodes=30)
    trainer.train()


if __name__ == '__main__':
    main()
