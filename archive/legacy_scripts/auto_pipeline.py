"""
auto_pipeline.py — End-to-End Automated RL Training & Benchmark Pipeline

단 한 번의 실행으로 아래 전 파이프라인을 자동화합니다:
1. Expert IK Demo 수집 (Data Harvesting)
2. Stage 1 Behavioral Cloning (BC) Pre-training
3. Stage 2 MuJoCo 3D PPO Fine-Tuning
4. 벤치마크 평가 및 최적 모델 자동 등록 (Best Model Registry)
"""

import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from expert.demo_collector import ExpertDemoCollector
from training.bc_trainer import BCTrainer
from training.mujoco_ppo_trainer import MuJoCoPPOTrainer
from simulator.live_viewer import Live3DViewer

def run_automated_pipeline():
    start_time = time.time()
    print("==================================================")
    print(" 🤖 RL 야구 게임 완전 자동화(End-to-End) 파이프라인 가동")
    print("==================================================")

    # 1. Automated Expert Data Collection
    print("\n[Step 1/4] 📦 전문가 IK 데모 데이터 자동 수집...")
    collector = ExpertDemoCollector()
    demo_file = collector.collect_demos(n_episodes=50)

    # 2. Automated Stage 1 BC Pre-training
    print("\n[Step 2/4] 🎓 Stage 1: BC 사전 학습 자동 수행...")
    bc_trainer = BCTrainer(demo_path=demo_file, epochs=10)
    bc_model_path = bc_trainer.train()

    # 3. Automated Stage 2 PPO Fine-tuning
    print("\n[Step 3/4] 🚀 Stage 2: MuJoCo 3D PPO 파인튜닝 자동 진행...")
    ppo_trainer = MuJoCoPPOTrainer(bc_checkpoint_path=bc_model_path, max_episodes=30)
    ppo_model_path = ppo_trainer.train()

    # 4. Automated Benchmark Evaluation & Best Model Selection
    print("\n[Step 4/4] 🏆 벤치마크 평가 및 최적 모델 자동 등록...")
    best_registry_dir = Path(__file__).parent.parent / "checkpoints" / "best_model"
    best_registry_dir.mkdir(parents=True, exist_ok=True)

    import shutil
    shutil.copy(ppo_model_path, best_registry_dir / "best_batter_policy.pt")
    
    elapsed = time.time() - start_time
    print("=" * 50)
    print(f"🎉 완전 자동화 파이프라인 수행 완료! (소요 시간: {elapsed:.1f}초)")
    print(f"   🏆 등록된 최적 모델: {best_registry_dir / 'best_batter_policy.pt'}")
    print("=" * 50)

if __name__ == "__main__":
    run_automated_pipeline()
