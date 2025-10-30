let moistureChart = null;

function initChart() {
    const ctx = document.getElementById('moistureChart').getContext('2d');
    moistureChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Bodenfeuchte (%)',
                data: [],
                borderColor: 'green',
                backgroundColor: 'rgba(0, 255, 0, 0.1)'
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function updateChart() {
    fetch('/api/sensors/Bodenfeuchte/history')
        .then(r => r.json())
        .then(data => {
            moistureChart.data.labels = data.map(d =>
                new Date(d.timestamp).toLocaleTimeString('de-DE')
            );
            moistureChart.data.datasets[0].data = data.map(d => d.value);
            moistureChart.update();
        })
        .catch(error => console.error('Fehler beim Laden des Charts:', error));
}

// Chart initialisieren und Updates starten
initChart();
updateChart();
setInterval(updateChart, 10000);
