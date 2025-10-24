import os
from flask import Flask, render_template, jsonify
from datetime import datetime, UTC
import threading
import time
import random
import paho.mqtt.client as mqtt


app = Flask(__name__)

# Datenbank konfigurieren
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///plant_sensors.db')

# Temporärer Speicher
latest_values = {
}

# MQTT-Konfiguration
MQTT_BROKER = "192.168.1.241"  # IP des Brokers
MQTT_PORT = 1883
MQTT_TOPIC = "paprika/sensor/moisture_percent"  # Topic

def on_connect(client, userdata, flags, rc):
    print(f"MQTT verbunden mit Code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()  # z.B. "42%"

        # Prozentzeichen entfernen und in Float umwandeln
        value = float(payload.replace('%', '').strip())

        update_sensor("Bodenfeuchte", round(value, 1))
        print(f"Empfangen: {payload} → Wert: {value}%")
    except ValueError:
        print(f"Ungültiger Wert: {msg.payload}")

def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

#Route zur index.html
@app.route('/')
def index():
    return render_template('index.html')


# API-Endpunkt: Gibt alle Sensordaten als JSON zurück
@app.route('/api/sensors')
def get_all_sensors():
    return jsonify(latest_values)


# API-Endpunkt: Gibt die Daten eines bestimmten Sensors als JSON zurück
@app.route('/api/sensors/<sensor_name>')
def get_sensor_data(sensor_name):
    if sensor_name in latest_values:
        return jsonify({sensor_name: latest_values[sensor_name]})
    else:
        return jsonify({'error': 'Sensor not found'}), 404


# Aktualisiert die Daten eines bestimmten Sensors
def update_sensor(sensor_name, value, timestamp=None):
    latest_values[sensor_name] = {
        'value': value,
        'timestamp': (timestamp or datetime.now(UTC).isoformat())
    }

def simulate_sensors():
    while True:
        # Simuliert realistische Schwankungen
        update_sensor("Bodenfeuchte", round(18 + random.uniform(-3, 5), 1))
        time.sleep(10)  # alle 10 Sekunden


if __name__ == '__main__':
    update_sensor("Bodenfeuchte", 0)  # Startwert

    # Startet MQTT im Hintergrund
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()

    app.run(debug=True, host='0.0.0.0', port=5000)
