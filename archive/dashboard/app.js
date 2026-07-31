const perfCtx = document.getElementById('performanceChart').getContext('2d');
const lossCtx = document.getElementById('lossChart').getContext('2d');

Chart.defaults.color = '#8B949E';
Chart.defaults.font.family = 'Inter';

const perfChart = new Chart(perfCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Batter Reward',
                borderColor: '#00E5FF',
                backgroundColor: 'rgba(0, 229, 255, 0.1)',
                data: [],
                yAxisID: 'y',
                fill: true,
                tension: 0.4
            },
            {
                label: 'Pitcher Reward',
                borderColor: '#FF5A5F',
                data: [],
                yAxisID: 'y',
                tension: 0.4
            },
            {
                label: 'Fielder Reward',
                borderColor: '#B000FF',
                data: [],
                yAxisID: 'y',
                tension: 0.4
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        scales: {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                grid: { color: 'rgba(255, 255, 255, 0.05)' }
            }
        }
    }
});

const lossChart = new Chart(lossCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            { label: 'Pitcher WM Loss', borderColor: '#FF5A5F', data: [], tension: 0.4 },
            { label: 'Batter WM Loss', borderColor: '#00E5FF', data: [], tension: 0.4 },
            { label: 'Fielder WM Loss', borderColor: '#B000FF', data: [], tension: 0.4 }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        scales: {
            y: { grid: { color: 'rgba(255, 255, 255, 0.05)' } }
        }
    }
});

let lastStatsLength = 0;
let lastVideoCount = 0;

async function fetchStats() {
    try {
        const res = await fetch('../logs/training_stats.json');
        const data = await res.json();
        
        if (data.episodes) {
            // If training was restarted, reset the tracker
            if (data.episodes.length < lastStatsLength) {
                lastStatsLength = 0;
            }
            
            if (data.episodes.length > lastStatsLength) {
                lastStatsLength = data.episodes.length;
                
                // Limit to last 50 points so the chart doesn't crowd or expand infinitely
                const MAX_POINTS = 50;
                const recentEpisodes = data.episodes.slice(-MAX_POINTS);

                const labels = recentEpisodes.map(e => `EP ${e.episode}`);
                perfChart.data.labels = labels;
                perfChart.data.datasets[0].data = recentEpisodes.map(e => e.reward_batter || 0);
                perfChart.data.datasets[1].data = recentEpisodes.map(e => e.reward_pitcher || 0);
                perfChart.data.datasets[2].data = recentEpisodes.map(e => e.reward_fielder || 0);
                perfChart.update();
                
                lossChart.data.labels = labels;
                lossChart.data.datasets[0].data = recentEpisodes.map(e => e.pitcher_wm_loss || 0);
                lossChart.data.datasets[1].data = recentEpisodes.map(e => e.batter_wm_loss || 0);
                lossChart.data.datasets[2].data = recentEpisodes.map(e => e.fielder_wm_loss || 0);
                lossChart.update();
                
                document.getElementById('trainingStatus').innerText = `Live: Episode ${data.episodes[data.episodes.length-1].episode}`;
            }
        }
    } catch (e) {
        console.warn("Waiting for stats JSON...");
    }
}

async function fetchVideos() {
    try {
        const res = await fetch('../videos/video_manifest.json');
        const data = await res.json();
        
        if (data.videos && data.videos.length > lastVideoCount) {
            lastVideoCount = data.videos.length;
            
            const gallery = document.getElementById('videoGallery');
            gallery.innerHTML = '';
            
            data.videos.forEach((vid, idx) => {
                const btn = document.createElement('button');
                btn.className = 'gallery-btn' + (idx === 0 ? ' active' : '');
                btn.innerText = `EP ${vid.episode}`;
                btn.onclick = () => {
                    document.querySelectorAll('.gallery-btn').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    loadVideo(vid);
                };
                gallery.appendChild(btn);
                
                if (idx === 0) loadVideo(vid);
            });
        }
    } catch (e) {
        console.warn("Waiting for video manifest...");
    }
}

function loadVideo(vid) {
    const videoEl = document.getElementById('mainVideo');
    const titleEl = document.getElementById('videoTitle');
    
    // Add cache buster to force reload
    const src = `../videos/${vid.filename}`;
    if (videoEl.src !== window.location.origin + src.substring(2)) {
        videoEl.src = src;
        titleEl.innerText = `Stage ${vid.stage} - Episode ${vid.episode}`;
    }
}

// Initial fetch
fetchStats();
fetchVideos();

// Poll every 3 seconds
setInterval(fetchStats, 3000);
setInterval(fetchVideos, 3000);
