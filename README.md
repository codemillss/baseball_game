# 🧠 PyTorch 딥러닝 마스터 워크북 & AI 활용 학습 저장소

[![PyTorch](https://img.shields.io/badge/PyTorch-2.13-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?style=for-the-badge&logo=jupyter&logoColor=white)](https://jupyter.org/)

딥러닝의 **기초 문법부터 차원 관리, 자동 미분(Autograd), 학습 전략 및 End-to-End 실전 분류기 구축**까지 단계별 문제 해결을 통해 딥러닝 메커니즘을 마스터하는 실습 저장소입니다.

생성형 AI(Antigravity, ChatGPT, Claude 등)를 **1:1 대화형 페어 프로그래머(Pair Programmer)**로 활용하며, 스스로 문제를 해결하고 풀이 과정을 기록하는 구조로 설계되었습니다.

---

## 📂 저장소 구조 (Repository Structure)

본 저장소는 **원본 문제 템플릿**과 **본인이 직접 풀이한 결과**를 명확히 분리하여 관리합니다.

```text
.
├── README.md                           # 프로젝트 설명 및 AI 학습 가이드 문서
├── DeepLearning_Workbook.ipynb         # [문제 템플릿] 풀어야 할 워크북 (Problem Template)
├── solutions/                          # [풀이 저장소] 본인이 직접 푼 파일 관리 폴더
│   └── DeepLearning_Workbook_Solved.ipynb # 내가 직접 푼 노트북 (My Solution)
├── requirements.txt                    # 의존성 패키지 목록
└── .gitignore                          # 가상환경 및 임시파일 관리
```

- **`DeepLearning_Workbook.ipynb`**: `### TODO: 코드 작성 ###` 빈칸과 자동 검증(`Assertion Test`) 코드가 포함된 원본 문제 파일입니다.
- **`solutions/DeepLearning_Workbook_Solved.ipynb`**: 문제들을 직접 풀고 검증을 통과한 나만의 학습 기록 및 정답 노트북입니다.

---

## 📘 모듈별 상세 커리큘럼 (Curriculum)

| 모듈 | 주제 | 핵심 개념 및 실습 문제 |
|:---:|---|---|
| **Module 1** | **PyTorch 기초 문법 & 텐서 연산** | 텐서 속성(`shape`, `dtype`, `device`), 원소별 연산 vs 행렬 곱(`@`, `torch.matmul`), Boolean Masking을 활용한 ReLU 동작 구현 |
| **Module 2** | **차원 관리 Masterclass** | `view()` vs `reshape()`, 메모리 연속성(`contiguous`), `unsqueeze()`, `squeeze()`, `permute()` (`NHWC` ↔ `NCHW`), 브로드캐스팅, `cat()` vs `stack()` |
| **Module 3** | **Autograd & 신경망 모듈** | `requires_grad=True`, `backward()`, 기울기 추적 수식 계산, `nn.Module` 상속 커스텀 다층 인공신경망(`SimpleMLP`) 설계 |
| **Module 4** | **학습 전략 및 실전 기법** | `CrossEntropyLoss` 입출력 규격 맞추기, `BatchNorm`, `Dropout`, `model.train()` vs `model.eval()`, `torch.no_grad()` 검증 루프 구현 |
| **Module 5** | **종합 실전 프로젝트** | 2D 데이터셋 ➔ 차원 정형화 ➔ 커스텀 `Classifier` ➔ Adam Optimizer & CrossEntropyLoss ➔ **5 Epoch 학습/검증 완전 자동화** |

---

## 🤖 생성형 AI (AI Pair Programmer) 활용 학습 전략

본 워크북은 단순히 답안을 복사하는 것이 아니라, **생성형 AI를 지능형 학습 조교로 활용하여 개념을 완벽히 이해하는 것**을 목표로 합니다.

### 💡 추천 질문/프롬프트 패턴

#### 1. 개념 이해가 막힐 때
> 💬 *"PyTorch에서 `view()`와 `reshape()`의 차이가 뭐야? 메모리 연속성(`is_contiguous()`) 개념과 함께 예시 코드로 설명해줘."*

#### 2. 차원(Shape) 조작이 헷갈릴 때
> 💬 *"이미지 텐서 모양이 `(32, 224, 224, 3)`인데 Conv2d 레이어에 넣으려면 `(32, 3, 224, 224)`로 바꿔야 해. 왜 `reshape` 대신 `permute`를 써야 하는지 차이점을 알려줘."*

#### 3. Assertion Error (채점 에러) 디버깅 시
> 💬 *"내가 작성한 코드가 `AssertionError: expected shape (32, 64) but got (32, 128)` 에러가 나는데, 어떤 부분에서 행렬 차원 계산이 잘못된 걸까?"*

---

## 🛠️ 빠른 시작 가이드 (Quick Start)

### 1. 저장소 클론 (Clone Repository)
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. 가상환경 생성 및 패키지 설치
```bash
# 파이썬 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화 (macOS/Linux)
source .venv/bin/activate

# Windows 가상환경 활성화
# .venv\Scripts\activate

# 필요한 딥러닝 패키지 한번에 설치
pip install -r requirements.txt
```

### 3. 주피터 노트북 실행 및 풀어보기
- **VS Code 사용 시**: VS Code에서 `DeepLearning_Workbook.ipynb` 열기 ➔ 우측 상단 `Select Kernel` ➔ `.venv` 선택 후 풀이 시작!
- **웹 브라우저 사용 시**:
  ```bash
  jupyter notebook
  ```

---

## 🏷️ License
본 프로젝트는 [MIT License](LICENSE)를 따릅니다. 딥러닝을 공부하는 모든 수강생 및 개발자들의 학습 용도로 자유롭게 활용할 수 있습니다.
