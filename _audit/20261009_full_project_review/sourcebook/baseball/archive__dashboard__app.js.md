# baseball/archive/dashboard/app.js

원본: [archive/dashboard/app.js](/Users/jin10000/Desktop/취업준비/원서_제출/02_핵심프로젝트_마스터풀/mini-project/baseball/archive/dashboard/app.js)

SHA256: `a58036db7401eae03e2ad8e5f0676c530335f91762294391e878e9a1c9554e57`

전체 162행. 원문은 생략 없이 보존했다. 함수 목록은 기계적으로 추출한 탐색 보조 자료이며, 설계 해설은 본문의 담당 장을 함께 읽는다.

## 전체 원문

````text
    1 | const perfCtx = document.getElementById('performanceChart').getContext('2d');
    2 | const lossCtx = document.getElementById('lossChart').getContext('2d');
    3 | 
    4 | Chart.defaults.color = '#8B949E';
    5 | Chart.defaults.font.family = 'Inter';
    6 | 
    7 | const perfChart = new Chart(perfCtx, {
    8 |     type: 'line',
    9 |     data: {
   10 |         labels: [],
   11 |         datasets: [
   12 |             {
   13 |                 label: 'Batter Reward',
   14 |                 borderColor: '#00E5FF',
   15 |                 backgroundColor: 'rgba(0, 229, 255, 0.1)',
   16 |                 data: [],
   17 |                 yAxisID: 'y',
   18 |                 fill: true,
   19 |                 tension: 0.4
   20 |             },
   21 |             {
   22 |                 label: 'Pitcher Reward',
   23 |                 borderColor: '#FF5A5F',
   24 |                 data: [],
   25 |                 yAxisID: 'y',
   26 |                 tension: 0.4
   27 |             },
   28 |             {
   29 |                 label: 'Fielder Reward',
   30 |                 borderColor: '#B000FF',
   31 |                 data: [],
   32 |                 yAxisID: 'y',
   33 |                 tension: 0.4
   34 |             }
   35 |         ]
   36 |     },
   37 |     options: {
   38 |         responsive: true,
   39 |         maintainAspectRatio: false,
   40 |         animation: { duration: 0 },
   41 |         scales: {
   42 |             y: {
   43 |                 type: 'linear',
   44 |                 display: true,
   45 |                 position: 'left',
   46 |                 grid: { color: 'rgba(255, 255, 255, 0.05)' }
   47 |             }
   48 |         }
   49 |     }
   50 | });
   51 | 
   52 | const lossChart = new Chart(lossCtx, {
   53 |     type: 'line',
   54 |     data: {
   55 |         labels: [],
   56 |         datasets: [
   57 |             { label: 'Pitcher WM Loss', borderColor: '#FF5A5F', data: [], tension: 0.4 },
   58 |             { label: 'Batter WM Loss', borderColor: '#00E5FF', data: [], tension: 0.4 },
   59 |             { label: 'Fielder WM Loss', borderColor: '#B000FF', data: [], tension: 0.4 }
   60 |         ]
   61 |     },
   62 |     options: {
   63 |         responsive: true,
   64 |         maintainAspectRatio: false,
   65 |         animation: { duration: 0 },
   66 |         scales: {
   67 |             y: { grid: { color: 'rgba(255, 255, 255, 0.05)' } }
   68 |         }
   69 |     }
   70 | });
   71 | 
   72 | let lastStatsLength = 0;
   73 | let lastVideoCount = 0;
   74 | 
   75 | async function fetchStats() {
   76 |     try {
   77 |         const res = await fetch('../logs/training_stats.json');
   78 |         const data = await res.json();
   79 |         
   80 |         if (data.episodes) {
   81 |             // If training was restarted, reset the tracker
   82 |             if (data.episodes.length < lastStatsLength) {
   83 |                 lastStatsLength = 0;
   84 |             }
   85 |             
   86 |             if (data.episodes.length > lastStatsLength) {
   87 |                 lastStatsLength = data.episodes.length;
   88 |                 
   89 |                 // Limit to last 50 points so the chart doesn't crowd or expand infinitely
   90 |                 const MAX_POINTS = 50;
   91 |                 const recentEpisodes = data.episodes.slice(-MAX_POINTS);
   92 | 
   93 |                 const labels = recentEpisodes.map(e => `EP ${e.episode}`);
   94 |                 perfChart.data.labels = labels;
   95 |                 perfChart.data.datasets[0].data = recentEpisodes.map(e => e.reward_batter || 0);
   96 |                 perfChart.data.datasets[1].data = recentEpisodes.map(e => e.reward_pitcher || 0);
   97 |                 perfChart.data.datasets[2].data = recentEpisodes.map(e => e.reward_fielder || 0);
   98 |                 perfChart.update();
   99 |                 
  100 |                 lossChart.data.labels = labels;
  101 |                 lossChart.data.datasets[0].data = recentEpisodes.map(e => e.pitcher_wm_loss || 0);
  102 |                 lossChart.data.datasets[1].data = recentEpisodes.map(e => e.batter_wm_loss || 0);
  103 |                 lossChart.data.datasets[2].data = recentEpisodes.map(e => e.fielder_wm_loss || 0);
  104 |                 lossChart.update();
  105 |                 
  106 |                 document.getElementById('trainingStatus').innerText = `Live: Episode ${data.episodes[data.episodes.length-1].episode}`;
  107 |             }
  108 |         }
  109 |     } catch (e) {
  110 |         console.warn("Waiting for stats JSON...");
  111 |     }
  112 | }
  113 | 
  114 | async function fetchVideos() {
  115 |     try {
  116 |         const res = await fetch('../videos/video_manifest.json');
  117 |         const data = await res.json();
  118 |         
  119 |         if (data.videos && data.videos.length > lastVideoCount) {
  120 |             lastVideoCount = data.videos.length;
  121 |             
  122 |             const gallery = document.getElementById('videoGallery');
  123 |             gallery.innerHTML = '';
  124 |             
  125 |             data.videos.forEach((vid, idx) => {
  126 |                 const btn = document.createElement('button');
  127 |                 btn.className = 'gallery-btn' + (idx === 0 ? ' active' : '');
  128 |                 btn.innerText = `EP ${vid.episode}`;
  129 |                 btn.onclick = () => {
  130 |                     document.querySelectorAll('.gallery-btn').forEach(b => b.classList.remove('active'));
  131 |                     btn.classList.add('active');
  132 |                     loadVideo(vid);
  133 |                 };
  134 |                 gallery.appendChild(btn);
  135 |                 
  136 |                 if (idx === 0) loadVideo(vid);
  137 |             });
  138 |         }
  139 |     } catch (e) {
  140 |         console.warn("Waiting for video manifest...");
  141 |     }
  142 | }
  143 | 
  144 | function loadVideo(vid) {
  145 |     const videoEl = document.getElementById('mainVideo');
  146 |     const titleEl = document.getElementById('videoTitle');
  147 |     
  148 |     // Add cache buster to force reload
  149 |     const src = `../videos/${vid.filename}`;
  150 |     if (videoEl.src !== window.location.origin + src.substring(2)) {
  151 |         videoEl.src = src;
  152 |         titleEl.innerText = `Stage ${vid.stage} - Episode ${vid.episode}`;
  153 |     }
  154 | }
  155 | 
  156 | // Initial fetch
  157 | fetchStats();
  158 | fetchVideos();
  159 | 
  160 | // Poll every 3 seconds
  161 | setInterval(fetchStats, 3000);
  162 | setInterval(fetchVideos, 3000);
````
