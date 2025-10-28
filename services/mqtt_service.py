import paho.mqtt.client as mqtt
import ssl
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 8883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

mqtt_client = None


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("✅ Erfolgreich mit HiveMQ Cloud verbunden!")
        client.subscribe("paprika/#")
    else:
        logger.error(f"❌ Verbindung fehlgeschlagen: Code {rc}")


def init_mqtt():
    global mqtt_client
    mqtt_client = mqtt.Client(client_id="flask-paprika-monitor")

    # Credentials setzen
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    # TLS/SSL aktivieren für HiveMQ Cloud
    mqtt_client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS
    )

    mqtt_client.on_connect = on_connect

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()
        logger.info(f"🚀 MQTT Client gestartet: {MQTT_BROKER}:{MQTT_PORT}")
    except Exception as e:
        logger.error(f"❌ MQTT Verbindung fehlgeschlagen: {e}")


def get_mqtt_client():
    return mqtt_client
