#include <Arduino.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include <WiFi.h>

// ReLight-X Edge Controller Board prototype firmware.
// Replace these placeholders with lab Wi-Fi and broker values before flashing.
const char *WIFI_SSID = "YOUR_WIFI_SSID";
const char *WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char *MQTT_HOST = "192.168.1.10";
const uint16_t MQTT_PORT = 1883;

const char *BOARD_ID = "board-001";
const char *LUMINAIRE_A_ID = "P001-A";
const char *LUMINAIRE_B_ID = "P001-B";

const uint8_t PWM_PIN_A = 18;
const uint8_t PWM_PIN_B = 19;
const uint8_t STATUS_LED_PIN = 2;
const uint8_t MANUAL_TEST_PIN = 27;
const uint8_t FAULT_INPUT_PIN = 26;

const uint8_t PWM_CHANNEL_A = 0;
const uint8_t PWM_CHANNEL_B = 1;
const uint32_t PWM_FREQ_HZ = 5000;
const uint8_t PWM_RESOLUTION_BITS = 10;
const uint16_t PWM_MAX_DUTY = (1 << PWM_RESOLUTION_BITS) - 1;

const float SAFE_FALLBACK_BRIGHTNESS = 0.70f;
const unsigned long MQTT_TIMEOUT_MS = 30000;
const unsigned long TELEMETRY_PERIOD_MS = 5000;

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

float brightnessA = 0.30f;
float brightnessB = 0.30f;
bool mqttHealthy = false;
bool localFault = false;
unsigned long lastMqttMessageMs = 0;
unsigned long lastTelemetryMs = 0;

float clampBrightness(float value) {
  if (value < 0.0f) return 0.0f;
  if (value > 1.0f) return 1.0f;
  return value;
}

void applyPwm(uint8_t channel, float brightness) {
  uint16_t duty = static_cast<uint16_t>(clampBrightness(brightness) * PWM_MAX_DUTY);
  ledcWrite(channel, duty);
}

void applyOutputs() {
  applyPwm(PWM_CHANNEL_A, brightnessA);
  applyPwm(PWM_CHANNEL_B, brightnessB);
}

void setLuminaireBrightness(const String &luminaireId, float value) {
  value = clampBrightness(value);
  if (luminaireId == LUMINAIRE_A_ID || luminaireId.endsWith("-A")) {
    brightnessA = value;
  }
  if (luminaireId == LUMINAIRE_B_ID || luminaireId.endsWith("-B")) {
    brightnessB = value;
  }
  applyOutputs();
}

void publishTelemetryFor(const char *luminaireId, float brightness) {
  StaticJsonDocument<384> doc;
  doc["board_id"] = BOARD_ID;
  doc["luminaire_id"] = luminaireId;
  doc["brightness"] = brightness;
  doc["pwm_duty_cycle"] = brightness;
  doc["simulated_output_voltage"] = brightness * 10.0f;
  doc["driver_temperature"] = 32.0f + brightness * 18.0f;
  doc["current_ma"] = 80.0f + brightness * 900.0f;
  doc["communication_health"] = mqttHealthy ? "ok" : "fallback";
  doc["fault_status"] = localFault ? "local_fault_input" : "ok";

  char payload[384];
  serializeJson(doc, payload);
  String topic = String("relightx/board/") + BOARD_ID + "/telemetry";
  mqtt.publish(topic.c_str(), payload);
}

void publishTelemetry() {
  publishTelemetryFor(LUMINAIRE_A_ID, brightnessA);
  publishTelemetryFor(LUMINAIRE_B_ID, brightnessB);
}

void handleCommand(const String &topic, const JsonDocument &doc) {
  const char *luminaireId = doc["luminaire_id"] | "";
  float brightness = doc["brightness"] | -1.0f;
  if (brightness < 0.0f) {
    brightness = doc["target_brightness"] | -1.0f;
  }
  if (brightness < 0.0f) {
    Serial.println("MQTT command ignored: missing brightness.");
    return;
  }

  String targetLuminaire = luminaireId;
  if (targetLuminaire.length() == 0) {
    if (topic.indexOf("/luminaire/") >= 0) {
      int start = topic.indexOf("/luminaire/") + 11;
      int end = topic.indexOf("/command", start);
      targetLuminaire = topic.substring(start, end);
    } else {
      targetLuminaire = LUMINAIRE_A_ID;
      setLuminaireBrightness(LUMINAIRE_B_ID, brightness);
    }
  }

  setLuminaireBrightness(targetLuminaire, brightness);
  Serial.printf("Brightness command %s -> %.2f\n", targetLuminaire.c_str(), brightness);
}

void mqttCallback(char *rawTopic, byte *payload, unsigned int length) {
  lastMqttMessageMs = millis();
  mqttHealthy = true;
  String topic = String(rawTopic);
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  if (error) {
    Serial.printf("Invalid JSON on %s\n", rawTopic);
    return;
  }
  handleCommand(topic, doc);
}

void connectWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("Connecting Wi-Fi SSID=%s\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.printf("\nWi-Fi connected: %s\n", WiFi.localIP().toString().c_str());
}

void subscribeTopics() {
  String boardTopic = String("relightx/board/") + BOARD_ID + "/command";
  mqtt.subscribe(boardTopic.c_str());
  mqtt.subscribe("relightx/luminaire/+/command");
  Serial.printf("Subscribed to %s and relightx/luminaire/+/command\n", boardTopic.c_str());
}

void connectMqtt() {
  if (mqtt.connected()) return;
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  String clientId = String("relightx-") + BOARD_ID;
  while (!mqtt.connected()) {
    Serial.printf("Connecting MQTT %s:%u\n", MQTT_HOST, MQTT_PORT);
    if (mqtt.connect(clientId.c_str())) {
      mqttHealthy = true;
      lastMqttMessageMs = millis();
      subscribeTopics();
      publishTelemetry();
    } else {
      mqttHealthy = false;
      Serial.printf("MQTT connection failed rc=%d; retrying\n", mqtt.state());
      delay(2000);
    }
  }
}

void applySafeFallbackIfNeeded() {
  localFault = digitalRead(FAULT_INPUT_PIN) == LOW;
  bool mqttTimedOut = (millis() - lastMqttMessageMs) > MQTT_TIMEOUT_MS;
  if (localFault || mqttTimedOut || !mqtt.connected()) {
    mqttHealthy = false;
    brightnessA = SAFE_FALLBACK_BRIGHTNESS;
    brightnessB = SAFE_FALLBACK_BRIGHTNESS;
    applyOutputs();
  }
}

void handleLocalTestMode() {
  if (digitalRead(MANUAL_TEST_PIN) == LOW) {
    float phase = (millis() % 5000) / 5000.0f;
    brightnessA = 0.30f + phase * 0.70f;
    brightnessB = 1.00f - phase * 0.70f;
    applyOutputs();
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(MANUAL_TEST_PIN, INPUT_PULLUP);
  pinMode(FAULT_INPUT_PIN, INPUT_PULLUP);

  ledcSetup(PWM_CHANNEL_A, PWM_FREQ_HZ, PWM_RESOLUTION_BITS);
  ledcSetup(PWM_CHANNEL_B, PWM_FREQ_HZ, PWM_RESOLUTION_BITS);
  ledcAttachPin(PWM_PIN_A, PWM_CHANNEL_A);
  ledcAttachPin(PWM_PIN_B, PWM_CHANNEL_B);
  applyOutputs();

  connectWifi();
  connectMqtt();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    mqttHealthy = false;
    connectWifi();
  }
  if (!mqtt.connected()) {
    connectMqtt();
  }

  mqtt.loop();
  handleLocalTestMode();
  applySafeFallbackIfNeeded();

  digitalWrite(STATUS_LED_PIN, mqttHealthy ? HIGH : (millis() / 250) % 2);

  if (millis() - lastTelemetryMs > TELEMETRY_PERIOD_MS) {
    lastTelemetryMs = millis();
    publishTelemetry();
  }
}
