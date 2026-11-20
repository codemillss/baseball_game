# baseball/archive/dashboard/style.css

원본: [archive/dashboard/style.css](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/dashboard/style.css)

SHA256: `99fb46ffedcb82a6e3016600ff6690b0019a2e6fe31eff952948e3715ea66031`

전체 203행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | :root {
    2 |     --bg-color: #0B0E14;
    3 |     --panel-bg: rgba(20, 25, 35, 0.7);
    4 |     --border-color: rgba(255, 255, 255, 0.1);
    5 |     --accent-cyan: #00E5FF;
    6 |     --accent-purple: #B000FF;
    7 |     --text-main: #FFFFFF;
    8 |     --text-muted: #8B949E;
    9 | }
   10 | 
   11 | * {
   12 |     margin: 0;
   13 |     padding: 0;
   14 |     box-sizing: border-box;
   15 | }
   16 | 
   17 | body {
   18 |     font-family: 'Inter', sans-serif;
   19 |     background-color: var(--bg-color);
   20 |     background-image: 
   21 |         radial-gradient(circle at 15% 50%, rgba(0, 229, 255, 0.05), transparent 25%),
   22 |         radial-gradient(circle at 85% 30%, rgba(176, 0, 255, 0.05), transparent 25%);
   23 |     color: var(--text-main);
   24 |     min-height: 100vh;
   25 |     overflow-y: auto; /* Allow scrolling on small screens to prevent cut-offs */
   26 | }
   27 | 
   28 | .dashboard-container {
   29 |     max-width: 1800px;
   30 |     margin: 0 auto;
   31 |     padding: 20px;
   32 |     min-height: 100vh;
   33 |     display: flex;
   34 |     flex-direction: column;
   35 | }
   36 | 
   37 | /* Glassmorphism */
   38 | .glass-panel {
   39 |     background: var(--panel-bg);
   40 |     backdrop-filter: blur(16px);
   41 |     -webkit-backdrop-filter: blur(16px);
   42 |     border: 1px solid var(--border-color);
   43 |     border-radius: 16px;
   44 |     padding: 24px;
   45 |     box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
   46 | }
   47 | 
   48 | /* Header */
   49 | header {
   50 |     display: flex;
   51 |     justify-content: space-between;
   52 |     align-items: center;
   53 |     margin-bottom: 24px;
   54 | }
   55 | 
   56 | .logo {
   57 |     display: flex;
   58 |     align-items: center;
   59 |     gap: 12px;
   60 | }
   61 | 
   62 | .pulse {
   63 |     width: 12px;
   64 |     height: 12px;
   65 |     background-color: var(--accent-cyan);
   66 |     border-radius: 50%;
   67 |     box-shadow: 0 0 12px var(--accent-cyan);
   68 |     animation: pulse-anim 2s infinite;
   69 | }
   70 | 
   71 | @keyframes pulse-anim {
   72 |     0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.7); }
   73 |     70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(0, 229, 255, 0); }
   74 |     100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 229, 255, 0); }
   75 | }
   76 | 
   77 | h1 {
   78 |     font-size: 1.5rem;
   79 |     font-weight: 800;
   80 |     letter-spacing: -0.5px;
   81 | }
   82 | 
   83 | h1 span {
   84 |     color: var(--text-muted);
   85 |     font-weight: 400;
   86 | }
   87 | 
   88 | .status-badge {
   89 |     padding: 8px 16px;
   90 |     background: rgba(0, 229, 255, 0.1);
   91 |     color: var(--accent-cyan);
   92 |     border: 1px solid rgba(0, 229, 255, 0.2);
   93 |     border-radius: 20px;
   94 |     font-size: 0.9rem;
   95 |     font-weight: 600;
   96 | }
   97 | 
   98 | /* Layout */
   99 | .grid-layout {
  100 |     display: grid;
  101 |     grid-template-columns: 1.2fr 0.8fr;
  102 |     gap: 24px;
  103 |     flex: 1;
  104 |     min-height: 0; /* Important for flex children bounds */
  105 | }
  106 | 
  107 | .mt-4 { margin-top: 0; }
  108 | 
  109 | h2 {
  110 |     font-size: 1.2rem;
  111 |     margin-bottom: 16px;
  112 |     color: var(--text-muted);
  113 | }
  114 | 
  115 | /* Video Section */
  116 | .video-section {
  117 |     display: flex;
  118 |     flex-direction: column;
  119 |     height: 100%;
  120 | }
  121 | 
  122 | .video-wrapper {
  123 |     flex: 1;
  124 |     width: 100%;
  125 |     border-radius: 12px;
  126 |     overflow: hidden;
  127 |     background: #000;
  128 |     border: 1px solid var(--border-color);
  129 |     display: flex;
  130 |     align-items: center;
  131 |     min-height: 0;
  132 | }
  133 | 
  134 | video {
  135 |     width: 100%;
  136 |     max-height: 100%;
  137 |     object-fit: contain;
  138 |     display: block;
  139 | }
  140 | 
  141 | .video-info {
  142 |     margin-top: 16px;
  143 | }
  144 | 
  145 | #videoTitle {
  146 |     font-size: 1.1rem;
  147 |     margin-bottom: 12px;
  148 |     color: var(--accent-cyan);
  149 | }
  150 | 
  151 | .video-gallery {
  152 |     display: flex;
  153 |     gap: 8px;
  154 |     overflow-x: auto;
  155 |     padding-bottom: 8px;
  156 | }
  157 | 
  158 | .gallery-btn {
  159 |     background: rgba(255, 255, 255, 0.05);
  160 |     border: 1px solid var(--border-color);
  161 |     color: var(--text-main);
  162 |     padding: 6px 12px;
  163 |     border-radius: 6px;
  164 |     cursor: pointer;
  165 |     white-space: nowrap;
  166 |     transition: all 0.2s;
  167 | }
  168 | 
  169 | .gallery-btn:hover {
  170 |     background: rgba(255, 255, 255, 0.1);
  171 | }
  172 | 
  173 | .gallery-btn.active {
  174 |     background: rgba(0, 229, 255, 0.2);
  175 |     border-color: var(--accent-cyan);
  176 |     color: var(--accent-cyan);
  177 | }
  178 | 
  179 | /* Charts */
  180 | .charts-section {
  181 |     display: flex;
  182 |     flex-direction: column;
  183 |     gap: 16px;
  184 |     height: 100%;
  185 |     min-height: 0;
  186 | }
  187 | 
  188 | .chart-container {
  189 |     flex: 1 1 0; 
  190 |     min-height: 250px; /* Ensure charts are never squished or chopped */
  191 |     display: flex;
  192 |     flex-direction: column;
  193 |     width: 100%;
  194 | }
  195 | 
  196 | .chart-wrapper {
  197 |     flex: 1;
  198 |     min-height: 0;
  199 |     position: relative;
  200 |     width: 100%;
  201 | }
  202 | 
  203 | 
````
