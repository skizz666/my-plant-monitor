#include <WiFi.h>
#include <PubSubClient.h>
#include <WiFiClientSecure.h>
#include <config.h>


// Sensor-Pin
const int sensorPin = 4; // GPIO4, wie in der Analyse empfohlen

// Kalibrierungswerte des Sensors
const int sensorDryValue = 3050; // trocken
const int sensorWetValue = 1232; // nass

// Globale Variablen
WiFiClientSecure espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
const long interval = 300000; 

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Verbinde mit ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status()!= WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WLAN verbunden");
  Serial.println("IP-Adresse: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Versuche, MQTT-Verbindung herzustellen...");
    String clientId = "ESP32Client-Paprika";

    // Mit HiveMQ Credentials verbinden
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("Verbunden mit HiveMQ Cloud!");
    } else {
      Serial.print("Fehlgeschlagen, rc=");
      Serial.print(client.state());
      Serial.println(" - versuche es in 5 Sekunden erneut");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  
  // Wichtiger Schritt: ADC-Konfiguration für den vollen Spannungsbereich
  // Dies stellt sicher, dass die gesamte Bandbreite des Sensorsignals gelesen werden kann.
 analogSetAttenuation(ADC_ATTEN_DB_11);

  setup_wifi();
  //TLS/SSL
  espClient.setInsecure();
  client.setServer(mqtt_server, 8883);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  unsigned long now = millis();
  if (now - lastMsg > interval) {
    lastMsg = now;

    // Sensorwert auslesen
    int rawValue = analogRead(sensorPin);
    Serial.print("Roher Sensorwert: ");
    Serial.println(rawValue);

    // Rohen Wert in einen Prozentwert umrechnen
    int moisturePercent = map(rawValue, sensorDryValue, sensorWetValue, 0, 100);
    moisturePercent = constrain(moisturePercent, 0, 100); // Sicherstellen, dass der Wert zwischen 0 und 100 liegt
    
    Serial.print("Bodenfeuchtigkeit: ");
    Serial.print(moisturePercent);
    Serial.println("%");

    // Prozentwert als String für MQTT vorbereiten
    char msg[10];
    char msg2[10];
    snprintf(msg, 10, "%d", moisturePercent);
    snprintf(msg2, 10, "%d", rawValue);

    // Prozentwert an den MQTT-Broker senden
    if (client.publish(mqtt_topic, msg)) {
      Serial.print("MQTT erfolgreich: ");
      Serial.print(moisturePercent);
      Serial.println("%");
    } else {
      Serial.println("MQTT fehlgeschlagen");
    }
    delay(5000);
    client.publish(mqtt_topic, msg2);

  }
}