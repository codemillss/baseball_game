# baseball/archive/legacy_training/bc_trainer.py

원본: [archive/legacy_training/bc_trainer.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_training/bc_trainer.py)

SHA256: `3ecabc2ed1fabefd5430eb20ae661a1f07eb9269b79e949f97f9c3dae20e03ac`

전체 117행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `BCTrainer` | ClassDef | 21 | 108 |
| `__init__` | FunctionDef | 24 | 67 |
| `train` | FunctionDef | 69 | 108 |
| `main` | FunctionDef | 111 | 113 |

## 전체 원문

````text
    1 | """
    2 | bc_trainer.py — Stage 1 Behavioral Cloning (BC) Pre-trainer
    3 | 
    4 | Supervised Learning 방식으로 Expert Demo 데이터셋(.npz)을 학습하여
    5 | Batter Policy 신경망의 초기 가중치를 지도학습(BC)으로 안정화시킵니다.
    6 | """
    7 | 
    8 | import os
    9 | from pathlib import Path
   10 | from typing import Optional, Tuple
   11 | 
   12 | import numpy as np
   13 | import torch
   14 | import torch.nn as nn
   15 | import torch.optim as optim
   16 | from torch.utils.data import TensorDataset, DataLoader
   17 | 
   18 | from training.networks import BatterPolicy, get_device
   19 | 
   20 | 
   21 | class BCTrainer:
   22 |     """Behavioral Cloning 지도학습 트레이너."""
   23 | 
   24 |     def __init__(
   25 |         self,
   26 |         demo_path: Optional[str] = None,
   27 |         lr: float = 1e-3,
   28 |         batch_size: int = 64,
   29 |         epochs: int = 20,
   30 |     ):
   31 |         if demo_path is None:
   32 |             demo_path = str(Path(__file__).parent.parent / "data" / "expert_demos" / "expert_demos.npz")
   33 | 
   34 |         self.demo_path = demo_path
   35 |         self.lr = lr
   36 |         self.batch_size = batch_size
   37 |         self.epochs = epochs
   38 |         self.device = get_device()
   39 | 
   40 |         # 데이터셋 로드
   41 |         if not os.path.exists(self.demo_path):
   42 |             raise FileNotFoundError(f"Expert demo dataset not found: {self.demo_path}")
   43 | 
   44 |         data = np.load(self.demo_path)
   45 |         obs_arr = data['observations']
   46 |         act_arr = data['actions']
   47 | 
   48 |         # Obs(15차원) -> BatterPolicy obs_dim=15, action_dim=3
   49 |         self.obs_dim = obs_arr.shape[-1]
   50 |         self.action_dim = act_arr.shape[-1]
   51 | 
   52 |         # PyTorch DataLoader 구축
   53 |         obs_tensor = torch.tensor(obs_arr, dtype=torch.float32)
   54 |         act_tensor = torch.tensor(act_arr, dtype=torch.float32)
   55 |         dataset = TensorDataset(obs_tensor, act_tensor)
   56 |         self.dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
   57 | 
   58 |         # Batter Policy 초기화
   59 |         self.policy = BatterPolicy(
   60 |             obs_dim=self.obs_dim,
   61 |             action_dim=self.action_dim,
   62 |             hidden_dim=128,
   63 |             num_layers=2,
   64 |         ).to(self.device)
   65 | 
   66 |         self.optimizer = optim.Adam(self.policy.parameters(), lr=self.lr)
   67 |         self.criterion = nn.MSELoss()
   68 | 
   69 |     def train(self, save_filename: str = "bc_batter_policy.pt") -> str:
   70 |         """BC 지도학습을 수행합니다."""
   71 |         print(f"🎓 Stage 1: Behavioral Cloning (BC) 학습 시작 ({self.epochs} epochs)...")
   72 |         print(f"   Device: {self.device} | Samples: {len(self.dataloader.dataset):,}")
   73 | 
   74 |         self.policy.train()
   75 |         for epoch in range(self.epochs):
   76 |             total_loss = 0.0
   77 |             n_batches = 0
   78 | 
   79 |             for obs_batch, act_batch in self.dataloader:
   80 |                 obs_batch = obs_batch.to(self.device)
   81 |                 act_batch = act_batch.to(self.device)
   82 | 
   83 |                 self.optimizer.zero_grad()
   84 |                 pred_mean, _, _ = self.policy(obs_batch)
   85 |                 loss = self.criterion(pred_mean, act_batch)
   86 |                 loss.backward()
   87 |                 self.optimizer.step()
   88 | 
   89 |                 total_loss += loss.item()
   90 |                 n_batches += 1
   91 | 
   92 |             avg_loss = total_loss / max(1, n_batches)
   93 |             if (epoch + 1) % max(1, self.epochs // 5) == 0:
   94 |                 print(f"   [Epoch {epoch+1:2d}/{self.epochs}] BC MSE Loss: {avg_loss:.6f}")
   95 | 
   96 |         # 저장
   97 |         save_dir = Path(__file__).parent.parent / "checkpoints"
   98 |         save_dir.mkdir(parents=True, exist_ok=True)
   99 |         save_path = save_dir / save_filename
  100 | 
  101 |         torch.save({
  102 |             'policy_state_dict': self.policy.state_dict(),
  103 |             'obs_dim': self.obs_dim,
  104 |             'action_dim': self.action_dim,
  105 |         }, save_path)
  106 | 
  107 |         print(f"💾 Stage 1 BC Base Policy 저장 완료: {save_path}\n")
  108 |         return str(save_path)
  109 | 
  110 | 
  111 | def main():
  112 |     trainer = BCTrainer(epochs=10)
  113 |     trainer.train()
  114 | 
  115 | 
  116 | if __name__ == '__main__':
  117 |     main()
````
