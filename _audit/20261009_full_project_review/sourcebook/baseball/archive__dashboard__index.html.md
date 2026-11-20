# baseball/archive/dashboard/index.html

원본: [archive/dashboard/index.html](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/dashboard/index.html)

SHA256: `eb49823def79fab0495a8a1e26a61e053ef460661b1c28f5dc153664ab7204e1`

전체 66행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | <!DOCTYPE html>
    2 | <html lang="ko">
    3 | <head>
    4 |     <meta charset="UTF-8">
    5 |     <meta name="viewport" content="width=device-width, initial-scale=1.0">
    6 |     <title>AI Baseball Dashboard</title>
    7 |     <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    8 |     <link rel="stylesheet" href="style.css?v=6">
    9 |     <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
   10 | </head>
   11 | <body>
   12 |     <div class="dashboard-container">
   13 |         <!-- Header -->
   14 |         <header class="glass-panel">
   15 |             <div class="logo">
   16 |                 <span class="pulse"></span>
   17 |                 <h1>AI Baseball <span>Training Center</span></h1>
   18 |             </div>
   19 |             <div class="status-badge" id="trainingStatus">
   20 |                 Polling Data...
   21 |             </div>
   22 |         </header>
   23 | 
   24 |         <!-- Main Grid -->
   25 |         <main class="grid-layout">
   26 |             <!-- Left Column: Video Player -->
   27 |             <section class="video-section glass-panel">
   28 |                 <h2>Latest Episode (1st Person View)</h2>
   29 |                 <div class="video-wrapper">
   30 |                     <video id="mainVideo" controls autoplay loop muted>
   31 |                         <source src="" type="video/mp4">
   32 |                         Your browser does not support the video tag.
   33 |                     </video>
   34 |                 </div>
   35 |                 <div class="video-info">
   36 |                     <h3 id="videoTitle">Waiting for video...</h3>
   37 |                     <div class="video-gallery" id="videoGallery">
   38 |                         <!-- Thumbnail buttons will be injected here -->
   39 |                     </div>
   40 |                 </div>
   41 |             </section>
   42 | 
   43 |             <!-- Right Column: Charts -->
   44 |             <section class="charts-section">
   45 |                 <!-- Top Chart: Contact Rate & Reward -->
   46 |                 <div class="chart-container glass-panel">
   47 |                     <h2>Multi-Agent Rewards</h2>
   48 |                     <div class="chart-wrapper">
   49 |                         <canvas id="performanceChart"></canvas>
   50 |                     </div>
   51 |                 </div>
   52 |                 
   53 |                 <!-- Bottom Chart: Losses -->
   54 |                 <div class="chart-container glass-panel mt-4">
   55 |                     <h2>Multi-Agent WM Losses</h2>
   56 |                     <div class="chart-wrapper">
   57 |                         <canvas id="lossChart"></canvas>
   58 |                     </div>
   59 |                 </div>
   60 |             </section>
   61 |         </main>
   62 |     </div>
   63 | 
   64 |     <script src="app.js?v=6"></script>
   65 | </body>
   66 | </html>
````
