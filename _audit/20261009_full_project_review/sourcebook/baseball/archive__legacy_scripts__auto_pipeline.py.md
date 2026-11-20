# baseball/archive/legacy_scripts/auto_pipeline.py

원본: [archive/legacy_scripts/auto_pipeline.py](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/legacy_scripts/auto_pipeline.py)

SHA256: `662b088c60315d6dc83f3c5f780274eb1c83db63ed82d5e23f1d113d91054f1e`

전체 60행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 클래스·함수 위치

| 이름 | 종류 | 시작행 | 끝행 |
|---|---|---:|---:|
| `run_automated_pipeline` | FunctionDef | 24 | 57 |

## 전체 원문

````text
    1 | """
    2 | auto_pipeline.py — End-to-End Automated RL Training & Benchmark Pipeline
    3 | 
    4 | 단 한 번의 실행으로 아래 전 파이프라인을 자동화합니다:
    5 | 1. Expert IK Demo 수집 (Data Harvesting)
    6 | 2. Stage 1 Behavioral Cloning (BC) Pre-training
    7 | 3. Stage 2 MuJoCo 3D PPO Fine-Tuning
    8 | 4. 벤치마크 평가 및 최적 모델 자동 등록 (Best Model Registry)
    9 | """
   10 | 
   11 | import os
   12 | import sys
   13 | import time
   14 | from pathlib import Path
   15 | 
   16 | # Add project root to sys.path
   17 | sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
   18 | 
   19 | from expert.demo_collector import ExpertDemoCollector
   20 | from training.bc_trainer import BCTrainer
   21 | from training.mujoco_ppo_trainer import MuJoCoPPOTrainer
   22 | from simulator.live_viewer import Live3DViewer
   23 | 
   24 | def run_automated_pipeline():
   25 |     start_time = time.time()
   26 |     print("==================================================")
   27 |     print(" 🤖 RL 야구 게임 완전 자동화(End-to-End) 파이프라인 가동")
   28 |     print("==================================================")
   29 | 
   30 |     # 1. Automated Expert Data Collection
   31 |     print("\n[Step 1/4] 📦 전문가 IK 데모 데이터 자동 수집...")
   32 |     collector = ExpertDemoCollector()
   33 |     demo_file = collector.collect_demos(n_episodes=50)
   34 | 
   35 |     # 2. Automated Stage 1 BC Pre-training
   36 |     print("\n[Step 2/4] 🎓 Stage 1: BC 사전 학습 자동 수행...")
   37 |     bc_trainer = BCTrainer(demo_path=demo_file, epochs=10)
   38 |     bc_model_path = bc_trainer.train()
   39 | 
   40 |     # 3. Automated Stage 2 PPO Fine-tuning
   41 |     print("\n[Step 3/4] 🚀 Stage 2: MuJoCo 3D PPO 파인튜닝 자동 진행...")
   42 |     ppo_trainer = MuJoCoPPOTrainer(bc_checkpoint_path=bc_model_path, max_episodes=30)
   43 |     ppo_model_path = ppo_trainer.train()
   44 | 
   45 |     # 4. Automated Benchmark Evaluation & Best Model Selection
   46 |     print("\n[Step 4/4] 🏆 벤치마크 평가 및 최적 모델 자동 등록...")
   47 |     best_registry_dir = Path(__file__).parent.parent / "checkpoints" / "best_model"
   48 |     best_registry_dir.mkdir(parents=True, exist_ok=True)
   49 | 
   50 |     import shutil
   51 |     shutil.copy(ppo_model_path, best_registry_dir / "best_batter_policy.pt")
   52 |     
   53 |     elapsed = time.time() - start_time
   54 |     print("=" * 50)
   55 |     print(f"🎉 완전 자동화 파이프라인 수행 완료! (소요 시간: {elapsed:.1f}초)")
   56 |     print(f"   🏆 등록된 최적 모델: {best_registry_dir / 'best_batter_policy.pt'}")
   57 |     print("=" * 50)
   58 | 
   59 | if __name__ == "__main__":
   60 |     run_automated_pipeline()
````
