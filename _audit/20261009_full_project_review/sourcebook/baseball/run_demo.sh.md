# baseball/run_demo.sh

원본: [run_demo.sh](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/run_demo.sh)

SHA256: `2afafc90df88ec128861a1ef86ea670d7144e2a7ecfafd4a3d741f70f22355e4`

전체 15행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | #!/bin/bash
    2 | echo "=================================================="
    3 | echo "⚾ STARTING AI BASEBALL SIMULATOR DEMO ⚾"
    4 | echo "=================================================="
    5 | echo "1. Simulating a Full Broadcast Match (Pitcher vs Batter)..."
    6 | .venv/bin/python cognitive_ai/evaluation/simulate_full_match.py
    7 | echo ""
    8 | echo "2. Simulating a Base Stealing Attempt..."
    9 | .venv/bin/python cognitive_ai/evaluation/evaluate_base_stealing.py
   10 | echo ""
   11 | echo "3. Simulating a full 9-Inning Game State Machine (Text)..."
   12 | .venv/bin/python cognitive_ai/evaluation/simulate_9_innings.py | head -n 25
   13 | echo "..."
   14 | echo ""
   15 | echo "✅ Demo Complete! Check the 'final_videos/' directory for rendered MP4s."
````
