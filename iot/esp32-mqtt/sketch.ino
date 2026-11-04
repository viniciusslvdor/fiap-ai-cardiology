// CardioIA - wearable sending vital signs over MQTT

#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "DHTesp.h"

const char* DEVICE_ID = "cardioia-wearable-01";
const char* PATIENT_ID = "P001";

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";
const char* MQTT_HOST = "broker.hivemq.com";
const uint16_t MQTT_PORT = 1883;
#define TOPIC_BASE "cardioia/vs26/P001"
const char* TOPIC_VITALS = TOPIC_BASE "/vitals";
const char* TOPIC_STATUS = TOPIC_BASE "/status";

const uint8_t PIN_DHT = 15;
const uint8_t PIN_BEAT_BUTTON = 4;
const uint8_t PIN_HR_POT = 34;
const uint8_t PIN_WIFI_SWITCH = 27;
const uint8_t PIN_LED_ONLINE = 25;
const uint8_t PIN_LED_ALERT = 26;
const uint8_t MPU_ADDR = 0x68;

const uint32_t SAMPLE_INTERVAL_MS = 2000;
const uint32_t MOTION_POLL_MS = 100;
const uint32_t DEBOUNCE_MS = 30;
const uint32_t WIFI_RETRY_MS = 15000;
const uint32_t MQTT_RETRY_MS = 5000;
const uint16_t MQTT_KEEPALIVE_S = 15;
const uint8_t FLUSH_BATCH = 10;

const size_t BUFFER_CAPACITY = 4000;

const uint32_t MIN_BEAT_INTERVAL_MS = 250;
const uint32_t MAX_BEAT_INTERVAL_MS = 2000;
const uint32_t BEAT_TIMEOUT_MS = 5000;
const uint8_t BEAT_AVG_WINDOW = 4;

const uint8_t BPM_HIGH = 120;
const uint8_t BPM_LOW = 50;
const float TEMP_HIGH_C = 38.0;
const float TEMP_LOW_C = 35.0;
const float FALL_IMPACT_G = 2.5;
const float MOTION_DELTA_G = 0.08;

const uint8_t ALERT_TACHYCARDIA = 1 << 0;
const uint8_t ALERT_BRADYCARDIA = 1 << 1;
const uint8_t ALERT_FEVER = 1 << 2;
const uint8_t ALERT_HYPOTHERMIA = 1 << 3;
const uint8_t ALERT_FALL = 1 << 4;
const uint8_t ALERT_MASK = 0x1F;
const uint8_t FLAG_MOVING = 1 << 5;
const uint8_t FLAG_BPM_SIMULATED = 1 << 6;
const uint8_t FLAG_SENSOR_ERROR = 1 << 7;

const int16_t TEMP_MISSING = INT16_MIN;

struct Reading {
  uint32_t seq;
  uint32_t capturedMs;
  int16_t tempC10;
  uint16_t humidity10;
  uint16_t stillSec;
  uint8_t bpm;
  uint8_t status;
};
static_assert(sizeof(Reading) == 16, "Reading must stay 16 bytes");

DHTesp dht;
WiFiClient netClient;
PubSubClient mqtt(netClient);
char mqttClientId[40];

Reading* ring = nullptr;
size_t ringHead = 0, ringCount = 0;
uint32_t nextSeq = 1;
uint32_t totalStored = 0, totalSent = 0, totalDiscarded = 0, totalThinned = 0, compactions = 0;
uint32_t sentThisSync = 0;
uint16_t storeStride = 1;

bool linkEnabled = false;
bool wifiStarted = false;
bool wasWifiUp = false;
uint32_t lastWifiAttemptMs = 0, lastMqttAttemptMs = 0;
bool mpuOk = false;

bool btnStable = HIGH, btnLastRaw = HIGH;
uint32_t btnChangedAt = 0, lastBeatMs = 0;
uint32_t beatIntervals[BEAT_AVG_WINDOW];
uint8_t beatIdx = 0, beatCount = 0;

float lastAx = 0, lastAy = 0, lastAz = 1;
float windowMaxDelta = 0, windowPeakG = 0, lastWindowPeakG = 0;
uint32_t lastMovementMs = 0;

uint32_t lastSampleMs = 0, lastMotionMs = 0;
uint8_t lastAlerts = 0;

size_t compactBuffer() {
  size_t write = 0;
  bool keepNormal = true;
  for (size_t read = 0; read < ringCount; read++) {
    const Reading r = ring[(ringHead + read) % BUFFER_CAPACITY];
    const bool isAlert = (r.status & ALERT_MASK) != 0;
    const bool keep = isAlert || keepNormal;
    if (!isAlert) keepNormal = !keepNormal;
    if (keep) ring[(ringHead + write++) % BUFFER_CAPACITY] = r;
  }
  const size_t removed = ringCount - write;
  ringCount = write;
  return removed;
}

void bufferPush(const Reading& r) {
  if (ringCount == BUFFER_CAPACITY) {
    size_t removed = compactBuffer();
    compactions++;
    if (removed == 0) {
      ringHead = (ringHead + 1) % BUFFER_CAPACITY;
      ringCount--;
      removed = 1;
    }
    totalDiscarded += removed;
    if (storeStride < 1024) storeStride *= 2;
    Serial.printf("[EDGE] Buffer full: %u readings discarded, now storing 1 of every %u normal readings\n",
                  (unsigned)removed, storeStride);
  }
  ring[(ringHead + ringCount) % BUFFER_CAPACITY] = r;
  ringCount++;
  totalStored++;
}

void pollBeatButton(uint32_t now) {
  const bool raw = digitalRead(PIN_BEAT_BUTTON);
  if (raw != btnLastRaw) {
    btnLastRaw = raw;
    btnChangedAt = now;
  }
  if (now - btnChangedAt < DEBOUNCE_MS || raw == btnStable) return;
  btnStable = raw;
  if (btnStable != LOW) return;

  const uint32_t interval = now - lastBeatMs;
  if (lastBeatMs != 0 && interval < MIN_BEAT_INTERVAL_MS) return;
  if (lastBeatMs != 0 && interval <= MAX_BEAT_INTERVAL_MS) {
    beatIntervals[beatIdx] = interval;
    beatIdx = (beatIdx + 1) % BEAT_AVG_WINDOW;
    if (beatCount < BEAT_AVG_WINDOW) beatCount++;
  } else {
    beatCount = 0;
  }
  lastBeatMs = now;
}

uint8_t readHeartRate(uint32_t now, bool& simulated) {
  if (beatCount >= 2 && now - lastBeatMs < BEAT_TIMEOUT_MS) {
    uint32_t sum = 0;
    for (uint8_t i = 0; i < beatCount; i++) sum += beatIntervals[i];
    simulated = false;
    return (uint8_t)constrain(60000UL * beatCount / sum, 30UL, 240UL);
  }
  simulated = true;
  const long base = map(analogRead(PIN_HR_POT), 0, 4095, 40, 180);
  return (uint8_t)constrain(base + random(-2, 3), 30L, 240L);
}

bool mpuBegin() {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B);
  Wire.write(0x00);
  return Wire.endTransmission() == 0;
}

bool mpuReadAccel(float& ax, float& ay, float& az) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((int)MPU_ADDR, 6) != 6) return false;
  int16_t raw[3];
  for (int i = 0; i < 3; i++) raw[i] = (Wire.read() << 8) | Wire.read();
  ax = raw[0] / 16384.0f;
  ay = raw[1] / 16384.0f;
  az = raw[2] / 16384.0f;
  return true;
}

void pollMotion(uint32_t now) {
  float ax, ay, az;
  if (!mpuOk || !mpuReadAccel(ax, ay, az)) return;
  const float delta = sqrtf(sq(ax - lastAx) + sq(ay - lastAy) + sq(az - lastAz));
  const float magnitude = sqrtf(sq(ax) + sq(ay) + sq(az));
  lastAx = ax;
  lastAy = ay;
  lastAz = az;
  windowMaxDelta = max(windowMaxDelta, delta);
  windowPeakG = max(windowPeakG, magnitude);
  if (delta > MOTION_DELTA_G) lastMovementMs = now;
}

Reading captureReading(uint32_t now) {
  Reading r = {};
  r.seq = nextSeq++;
  r.capturedMs = now;

  TempAndHumidity th = dht.getTempAndHumidity();
  if (dht.getStatus() == DHTesp::ERROR_NONE && !isnan(th.temperature)) {
    r.tempC10 = (int16_t)lroundf(th.temperature * 10);
    r.humidity10 = (uint16_t)lroundf(th.humidity * 10);
  } else {
    r.tempC10 = TEMP_MISSING;
    r.status |= FLAG_SENSOR_ERROR;
  }

  bool simulated = false;
  r.bpm = readHeartRate(now, simulated);
  if (simulated) r.status |= FLAG_BPM_SIMULATED;

  if (!mpuOk) r.status |= FLAG_SENSOR_ERROR;
  if (windowMaxDelta > MOTION_DELTA_G) r.status |= FLAG_MOVING;
  r.stillSec = (uint16_t)min((now - lastMovementMs) / 1000UL, 65535UL);

  if (r.bpm > BPM_HIGH) r.status |= ALERT_TACHYCARDIA;
  if (r.bpm < BPM_LOW) r.status |= ALERT_BRADYCARDIA;
  if (r.tempC10 != TEMP_MISSING) {
    if (r.tempC10 >= TEMP_HIGH_C * 10) r.status |= ALERT_FEVER;
    if (r.tempC10 < TEMP_LOW_C * 10) r.status |= ALERT_HYPOTHERMIA;
  }
  if (windowPeakG > FALL_IMPACT_G && lastWindowPeakG <= FALL_IMPACT_G) r.status |= ALERT_FALL;

  lastWindowPeakG = windowPeakG;
  windowMaxDelta = 0;
  windowPeakG = 0;
  return r;
}

void alertNames(uint8_t status, char* out, size_t len) {
  static const char* NAMES[] = {"TACHYCARDIA", "BRADYCARDIA", "FEVER", "HYPOTHERMIA", "FALL"};
  out[0] = '\0';
  for (int i = 0; i < 5; i++) {
    if (!(status & (1 << i))) continue;
    if (out[0]) strlcat(out, ",", len);
    strlcat(out, NAMES[i], len);
  }
}

void toJson(const Reading& r, uint32_t now, size_t buffered, char* out, size_t len) {
  char alerts[64];
  alertNames(r.status, alerts, sizeof(alerts));
  char alertsJson[96] = "";
  if (alerts[0]) {
    String s = String("\"") + alerts + "\"";
    s.replace(",", "\",\"");
    strlcpy(alertsJson, s.c_str(), sizeof(alertsJson));
  }
  char temp[12], hum[12];
  if (r.tempC10 == TEMP_MISSING) {
    strcpy(temp, "null");
    strcpy(hum, "null");
  } else {
    snprintf(temp, sizeof(temp), "%.1f", r.tempC10 / 10.0);
    snprintf(hum, sizeof(hum), "%.1f", r.humidity10 / 10.0);
  }
  snprintf(out, len,
           "{\"device\":\"%s\",\"patient\":\"%s\",\"seq\":%lu,\"age_s\":%lu,"
           "\"bpm\":%u,\"bpm_source\":\"%s\",\"temp_c\":%s,\"humidity\":%s,"
           "\"moving\":%s,\"still_s\":%u,\"alerts\":[%s],\"buffered\":%u}",
           DEVICE_ID, PATIENT_ID, (unsigned long)r.seq, (unsigned long)((now - r.capturedMs) / 1000), r.bpm,
           (r.status & FLAG_BPM_SIMULATED) ? "simulated" : "button", temp, hum,
           (r.status & FLAG_MOVING) ? "true" : "false", r.stillSec, alertsJson, (unsigned)buffered);
}

bool isOnline() { return linkEnabled && WiFi.status() == WL_CONNECTED && mqtt.connected(); }

void connectMqtt() {
  Serial.printf("[MQTT] Connecting to %s:%u as %s...\n", MQTT_HOST, MQTT_PORT, mqttClientId);
  if (mqtt.connect(mqttClientId, TOPIC_STATUS, 1, true, "offline")) {
    mqtt.publish(TOPIC_STATUS, "online", true);
    Serial.printf("[MQTT] Connected. %u readings waiting\n", (unsigned)ringCount);
  } else {
    Serial.printf("[MQTT] Failed (state %d), retrying in %lu s\n", mqtt.state(),
                  (unsigned long)(MQTT_RETRY_MS / 1000));
  }
}

void manageNetwork(uint32_t now) {
  const bool sw = digitalRead(PIN_WIFI_SWITCH) == HIGH;
  if (sw != linkEnabled) {
    linkEnabled = sw;
    if (!linkEnabled) {
      Serial.println("[NET] Switch off: network lost");
      netClient.stop();
      WiFi.disconnect();
      wifiStarted = false;
    } else {
      Serial.println("[NET] Switch on: network back");
    }
  }

  const bool wifiUp = WiFi.status() == WL_CONNECTED;
  if (wifiUp != wasWifiUp) {
    wasWifiUp = wifiUp;
    if (wifiUp) Serial.printf("[NET] Wi-Fi connected, IP %s\n", WiFi.localIP().toString().c_str());
    else Serial.println("[NET] Wi-Fi down. Readings stay in the local buffer");
  }
  if (!linkEnabled) return;

  if (!wifiUp) {
    if (!wifiStarted || now - lastWifiAttemptMs >= WIFI_RETRY_MS) {
      Serial.printf("[NET] Connecting to \"%s\"...\n", WIFI_SSID);
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);
      wifiStarted = true;
      lastWifiAttemptMs = now;
    }
    return;
  }

  if (!mqtt.connected()) {
    if (lastMqttAttemptMs == 0 || now - lastMqttAttemptMs >= MQTT_RETRY_MS) {
      lastMqttAttemptMs = now;
      connectMqtt();
    }
    return;
  }
  mqtt.loop();
}

void syncToCloud(uint32_t now) {
  if (!isOnline() || ringCount == 0) return;
  char json[320];
  for (uint8_t i = 0; i < FLUSH_BATCH && ringCount > 0; i++) {
    const Reading& r = ring[ringHead];
    toJson(r, now, ringCount - 1, json, sizeof(json));
    if (!mqtt.publish(TOPIC_VITALS, json)) {
      Serial.println("[MQTT] Publish failed, will retry");
      return;
    }
    if (ringCount == 1 && sentThisSync == 0) {
      Serial.printf("[MQTT] -> vitals #%lu | BPM %u | T %.1f C%s\n", (unsigned long)r.seq, r.bpm,
                    r.tempC10 == TEMP_MISSING ? NAN : r.tempC10 / 10.0, (r.status & ALERT_MASK) ? " | ALERT" : "");
    }
    ringHead = (ringHead + 1) % BUFFER_CAPACITY;
    ringCount--;
    totalSent++;
    sentThisSync++;
  }
  if (ringCount == 0) {
    storeStride = 1;
    if (sentThisSync > 1) Serial.printf("[SYNC] %lu buffered readings published\n", (unsigned long)sentThisSync);
    sentThisSync = 0;
  }
}

void printStats() {
  Serial.printf("[STATS] buffer %u/%u | stored %lu | sent %lu | discarded %lu | not stored %lu | "
                "compactions %lu | storing 1/%u | link %s | wifi %s | mqtt %s\n",
                (unsigned)ringCount, (unsigned)BUFFER_CAPACITY, (unsigned long)totalStored, (unsigned long)totalSent,
                (unsigned long)totalDiscarded, (unsigned long)totalThinned, (unsigned long)compactions, storeStride,
                linkEnabled ? "on" : "off", WiFi.status() == WL_CONNECTED ? "up" : "down",
                mqtt.connected() ? "up" : "down");
}

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println();
  Serial.println("[BOOT] CardioIA wearable - MQTT mode");

  pinMode(PIN_BEAT_BUTTON, INPUT_PULLUP);
  pinMode(PIN_WIFI_SWITCH, INPUT);
  pinMode(PIN_LED_ONLINE, OUTPUT);
  pinMode(PIN_LED_ALERT, OUTPUT);
  analogReadResolution(12);
  randomSeed(esp_random());

  dht.setup(PIN_DHT, DHTesp::DHT22);
  Wire.begin(21, 22);
  mpuOk = mpuBegin();
  Serial.printf("[BOOT] MPU6050 %s\n", mpuOk ? "ok" : "NOT FOUND");

  ring = (Reading*)malloc(BUFFER_CAPACITY * sizeof(Reading));
  if (!ring) {
    Serial.println("[BOOT] Could not allocate the buffer");
    while (true) delay(1000);
  }

  WiFi.mode(WIFI_STA);
  uint8_t mac[6];
  WiFi.macAddress(mac);
  snprintf(mqttClientId, sizeof(mqttClientId), "cardioia-%02x%02x%02x", mac[3], mac[4], mac[5]);
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);
  mqtt.setKeepAlive(MQTT_KEEPALIVE_S);
  mqtt.setSocketTimeout(5);

  lastMovementMs = millis();
}

void loop() {
  const uint32_t now = millis();

  pollBeatButton(now);
  manageNetwork(now);
  digitalWrite(PIN_LED_ONLINE, isOnline() ? HIGH : LOW);

  if (now - lastMotionMs >= MOTION_POLL_MS) {
    lastMotionMs = now;
    pollMotion(now);
  }

  if (now - lastSampleMs >= SAMPLE_INTERVAL_MS) {
    lastSampleMs = now;
    const Reading r = captureReading(now);
    const uint8_t alerts = r.status & ALERT_MASK;

    if (alerts || r.seq % storeStride == 0) bufferPush(r);
    else totalThinned++;

    digitalWrite(PIN_LED_ALERT, alerts ? HIGH : LOW);
    char names[64];
    alertNames(r.status, names, sizeof(names));
    if (alerts && alerts != lastAlerts) Serial.printf("[ALERT] %s\n", names);
    if (!alerts && lastAlerts) Serial.println("[ALERT] cleared");
    lastAlerts = alerts;

    if (!isOnline()) {
      Serial.printf("[EDGE] #%lu stored offline | BPM %u | T %.1f C | buffer %u/%u\n", (unsigned long)r.seq, r.bpm,
                    r.tempC10 == TEMP_MISSING ? NAN : r.tempC10 / 10.0, (unsigned)ringCount,
                    (unsigned)BUFFER_CAPACITY);
    }
  }

  syncToCloud(now);

  if (Serial.available()) {
    const char c = Serial.read();
    if (c == 's' || c == 'S') printStats();
  }
}
