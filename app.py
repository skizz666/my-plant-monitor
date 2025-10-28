import os
from flask import Flask, render_template, jsonify, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC
import threading
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from database import db
from models import User, SensorData
import ssl

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Datenbank konfigurieren
DATABASE_URL = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# login manager konfigurieren
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db.init_app(app)

@login_manager.user_loader
def user_load(user_id):
    return db.session.get(User, int(user_id))


# Temporärer Speicher
latest_values = {
}

# MQTT-Konfiguration
MQTT_BROKER = os.environ.get('MQTT_BROKER', '192.168.1.241')
MQTT_PORT = int(os.environ.get('MQTT_PORT', 1883))
MQTT_USER = os.environ.get('MQTT_USER')
MQTT_PASSWORD = os.environ.get('MQTT_PASSWORD')
MQTT_TOPIC = "paprika/sensor/moisture_percent"

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("MQTT verbunden mit HiveMQ!")
        # Alle Topics abonnieren(skalierbarkeit)
        client.subscribe("paprika/#")
    else:
        print(f"MQTT Verbindungsfehler, Code:{reason_code}")

def on_message(client, userdata, msg):
    try:
        with app.app_context():
            topic = msg.topic
            payload = msg.payload.decode()

            if "moisture" in topic:
                value = float(payload.replace('%', '').strip())
                update_sensor("Bodenfeuchte", round(value, 1))
                print(f"Empfangen: {payload} → Wert: {value}%")

                #Sensordaten in datenbank schreiben
                sensor_data = SensorData(
                    sensor_name="Bodenfeuchte",
                    value=value,
                    timestamp=datetime.now(UTC)
                )
                db.session.add(sensor_data)
                db.session.commit()

            else:
                print(f"Unbekanntes Topic: {topic}")

    except ValueError:
        print(f"Ungültiger Wert: {msg.payload}")

def start_mqtt():
    with app.app_context():
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = on_connect
        client.on_message = on_message

        #HiveMQTT
        if MQTT_USER and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

        #HiveMQTT TLS
        if MQTT_PORT == 8883:
            client.tls_set(
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS
            )

        try:
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            print(f"Verbinde mit {MQTT_BROKER}:{MQTT_PORT}...")
            client.loop_forever()
        except Exception as e:
            print(f"MQTT Verbindung fehlgeschlagen: {e}")

# Route zum Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:       #wenn user schon eingeloggt, ab zur index
        return redirect(url_for('index'))

    if request.method == 'POST':                    #logindaten durch request form eingeben
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Ungültiger Benutzername oder Passwort')  #fehlermeldung bei falschen daten

    return render_template('login.html')

# Route zum Logout
@app.route('/logout')
@login_required #nur eingeloggte user können ausloggen
def logout():
    logout_user()
    flash('Erfolgreich ausgeloggt', 'success')
    return redirect(url_for('login'))


#Route zur index.html
@app.route('/')
@login_required
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


if __name__ == '__main__':
    update_sensor("Bodenfeuchte", 0)  # Startwert

    # Startet MQTT im Hintergrund
    mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_thread.start()

    app.run(debug=True, host='0.0.0.0', port=5000)
