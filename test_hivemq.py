# test_hivemq.py
import paho.mqtt.client as mqtt
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Erfolgreich mit HiveMQ verbunden!")
        client.publish("test/hello", "Hello from Python!")
    else:
        print(f"❌ Verbindung fehlgeschlagen: {rc}")

client = mqtt.Client(client_id="test-python-client")
client.username_pw_set(os.getenv("MQTT_USER"), os.getenv("MQTT_PASSWORD"))
client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
client.on_connect = on_connect

client.connect(os.getenv("MQTT_BROKER"), int(os.getenv("MQTT_PORT")), 60)
client.loop_start()

import time
time.sleep(3)
client.disconnect()