# baseball/run_dashboard.sh

원본: [run_dashboard.sh](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/run_dashboard.sh)

SHA256: `8a582c6ac1d3a091ee4294de9bd574a484bd8b2b2634ce3c20e2962cc47745dc`

전체 9행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | #!/bin/bash
    2 | echo "=========================================================="
    3 | echo " 🚀 AI Baseball Training Dashboard Starting..."
    4 | echo "=========================================================="
    5 | echo " 1. Open your browser to: http://localhost:8000/dashboard"
    6 | echo " 2. Run the training script in another terminal to see live updates."
    7 | echo "=========================================================="
    8 | echo "Press Ctrl+C to stop."
    9 | python3 -m http.server 8000
````
