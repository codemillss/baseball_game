"""
bc_trainer.py — Stage 1 Behavioral Cloning (BC) Pre-trainer

Supervised Learning 방식으로 Expert Demo 데이터셋(.npz)을 학습하여
Batter Policy 신경망의 초기 가중치를 지도학습(BC)으로 안정화시킵니다.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

from training.networks import BatterPolicy, get_device


class BCTrainer:
    """Behavioral Cloning 지도학습 트레이너."""

    def __init__(
        self,
        demo_path: Optional[str] = None,
        lr: float = 1e-3,
        batch_size: int = 64,
        epochs: int = 20,
    ):
        if demo_path is None:
            demo_path = str(Path(__file__).parent.parent / "data" / "expert_demos" / "expert_demos.npz")

        self.demo_path = demo_path
        self.lr = lr
        self.batch_size = batch_size
        self.epochs = epochs
        self.device = get_device()

        # 데이터셋 로드
        if not os.path.exists(self.demo_path):
            raise FileNotFoundError(f"Expert demo dataset not found: {self.demo_path}")

        data = np.load(self.demo_path)
        obs_arr = data['observations']
        act_arr = data['actions']

        # Obs(15차원) -> BatterPolicy obs_dim=15, action_dim=3
        self.obs_dim = obs_arr.shape[-1]
        self.action_dim = act_arr.shape[-1]

        # PyTorch DataLoader 구축
        obs_tensor = torch.tensor(obs_arr, dtype=torch.float32)
        act_tensor = torch.tensor(act_arr, dtype=torch.float32)
        dataset = TensorDataset(obs_tensor, act_tensor)
        self.dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        # Batter Policy 초기화
        self.policy = BatterPolicy(
            obs_dim=self.obs_dim,
            action_dim=self.action_dim,
            hidden_dim=128,
            num_layers=2,
        ).to(self.device)

        self.optimizer = optim.Adam(self.policy.parameters(), lr=self.lr)
        self.criterion = nn.MSELoss()

    def train(self, save_filename: str = "bc_batter_policy.pt") -> str:
        """BC 지도학습을 수행합니다."""
        print(f"🎓 Stage 1: Behavioral Cloning (BC) 학습 시작 ({self.epochs} epochs)...")
        print(f"   Device: {self.device} | Samples: {len(self.dataloader.dataset):,}")

        self.policy.train()
        for epoch in range(self.epochs):
            total_loss = 0.0
            n_batches = 0

            for obs_batch, act_batch in self.dataloader:
                obs_batch = obs_batch.to(self.device)
                act_batch = act_batch.to(self.device)

                self.optimizer.zero_grad()
                pred_mean, _, _ = self.policy(obs_batch)
                loss = self.criterion(pred_mean, act_batch)
                loss.backward()
                self.optimizer.step()

                total_loss += loss.item()
                n_batches += 1

            avg_loss = total_loss / max(1, n_batches)
            if (epoch + 1) % max(1, self.epochs // 5) == 0:
                print(f"   [Epoch {epoch+1:2d}/{self.epochs}] BC MSE Loss: {avg_loss:.6f}")

        # 저장
        save_dir = Path(__file__).parent.parent / "checkpoints"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / save_filename

        torch.save({
            'policy_state_dict': self.policy.state_dict(),
            'obs_dim': self.obs_dim,
            'action_dim': self.action_dim,
        }, save_path)

        print(f"💾 Stage 1 BC Base Policy 저장 완료: {save_path}\n")
        return str(save_path)


def main():
    trainer = BCTrainer(epochs=10)
    trainer.train()


if __name__ == '__main__':
    main()
