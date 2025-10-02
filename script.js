// AquaFlow Dashboard JavaScript
// Fetches data from Flask API and updates dashboard UI

function fetchCurrentData() {
    fetch('/api/current-data')
        .then(res => res.json())
        .then(data => {
            document.getElementById('waterLevel').textContent = `${data.water_level_percent}%`;
            document.getElementById('distanceCm').textContent = `${data.distance_cm} cm`;
            document.getElementById('currentVolume').textContent = `${data.current_volume_liters} L`;
            document.getElementById('pumpRuntime').textContent = `${data.pump_runtime_seconds}s`;
            document.getElementById('sessionDuration').textContent = `${data.session_duration}s`;
            document.getElementById('metricLevel').textContent = `${data.water_level_percent}%`;
            document.getElementById('metricVolume').textContent = `${data.current_volume_liters}L`;
            document.getElementById('metricPumpStatus').textContent = data.pump_status;
            document.getElementById('metricRuntime').textContent = `${data.pump_runtime_seconds}s`;
            // Pump badge
            const badge = document.getElementById('pumpStatusBadge');
            badge.classList.toggle('active', data.pump_status === 'ON');
            badge.querySelector('.status-text').textContent = data.pump_status === 'ON' ? 'RUNNING' : 'IDLE';
            // Hide loading overlay
            document.getElementById('loadingOverlay').classList.add('hidden');
            // Last update
            document.getElementById('lastUpdate').textContent = `Last update: ${new Date().toLocaleTimeString()}`;
        });
}

function fetchStats() {
    fetch('/api/stats')
        .then(res => res.json())
        .then(stats => {
            document.getElementById('statMaxLevel').textContent = stats.max_level ? `${stats.max_level}%` : '0%';
            document.getElementById('statMinLevel').textContent = stats.min_level ? `${stats.min_level}%` : '0%';
            document.getElementById('statAvgLevel').textContent = stats.avg_level ? `${stats.avg_level.toFixed(1)}%` : '0%';
            document.getElementById('statDataPoints').textContent = stats.total_records || '0';
        });
}

function fetchHistory() {
    fetch('/api/history')
        .then(res => res.json())
        .then(history => {
            if (window.levelChart && history.levels) {
                levelChart.data.labels = history.timestamps;
                levelChart.data.datasets[0].data = history.levels;
                levelChart.update();
            }
        });
}

// Chart.js setup
let levelChart;
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('levelChart').getContext('2d');
    levelChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Water Level (%)',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59,130,246,0.1)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { min: 0, max: 100 }
            }
        }
    });
    // Initial fetch
    fetchCurrentData();
    fetchStats();
    fetchHistory();
    // Poll every 2 seconds
    setInterval(() => {
        fetchCurrentData();
        fetchStats();
        fetchHistory();
    }, 2000);
});

// Theme toggle
const themeSwitch = document.getElementById('themeSwitch');
themeSwitch.addEventListener('click', function() {
    const theme = document.documentElement.getAttribute('data-theme');
    document.documentElement.setAttribute('data-theme', theme === 'dark' ? 'light' : 'dark');
});
