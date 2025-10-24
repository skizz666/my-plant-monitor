// Sensordaten alle 2 Sekunden aktualisieren
function loadSensors() {
    fetch('/api/sensors')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('sensors-container');
            container.innerHTML = '';

            for (const [name, sensor] of Object.entries(data)) {
                const card = document.createElement('div');
                card.className = 'sensor-card';

                const timestamp = new Date(sensor.timestamp).toLocaleString('de-DE');

                card.innerHTML = `
                    <div class="sensor-name">${name}</div>
                    <div class="sensor-value">${sensor.value}%</div>
                    <div class="sensor-timestamp">Letzte Aktualisierung: ${timestamp}</div>
                `;

                container.appendChild(card);
            }
        })
        .catch(error => console.error('Fehler beim Laden der Sensordaten:', error));
}

// Beim Laden der Seite starten
loadSensors();
// Alle 2 Sekunden aktualisieren
setInterval(loadSensors, 10*1000);
