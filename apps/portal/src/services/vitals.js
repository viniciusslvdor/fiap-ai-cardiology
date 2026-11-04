/** Wearable data received over MQTT and the alert limits (same values used on the ESP32 and in Node-RED). */

export const MQTT_URL = import.meta.env.VITE_MQTT_URL ?? 'wss://broker.hivemq.com:8884/mqtt';
export const TOPIC_ROOT = import.meta.env.VITE_MQTT_TOPIC_ROOT ?? 'cardioia/vs26';

export const LIMITS = {
  bpmHigh: 120,
  bpmWarn: 100,
  bpmLow: 50,
  tempHigh: 38,
  tempWarn: 37.5,
  tempLow: 35,
};

export const LIVE_MAX_AGE_S = 10;
export const WINDOW_MS = 15 * 60 * 1000;

export function heartRateLevel(bpm) {
  if (bpm > LIMITS.bpmHigh || bpm < LIMITS.bpmLow) return 'alert';
  if (bpm > LIMITS.bpmWarn) return 'warning';
  return 'normal';
}

export function temperatureLevel(temp) {
  if (temp == null) return 'warning';
  if (temp >= LIMITS.tempHigh || temp < LIMITS.tempLow) return 'alert';
  if (temp >= LIMITS.tempWarn) return 'warning';
  return 'normal';
}

/** Returns { level: 'normal' | 'warning' | 'alert', reasons, alertCodes } for one reading. */
export function assessReading(r) {
  const reasons = [];
  const alertCodes = [];
  let level = 'normal';
  const raise = (lvl, code, text) => {
    reasons.push(text);
    if (lvl === 'alert') alertCodes.push(code);
    if (lvl === 'alert' || level === 'normal') level = lvl;
  };

  if (r.bpm > LIMITS.bpmHigh) raise('alert', 'TACHYCARDIA', `Tachycardia: ${r.bpm} bpm`);
  else if (r.bpm < LIMITS.bpmLow) raise('alert', 'BRADYCARDIA', `Bradycardia: ${r.bpm} bpm`);
  else if (r.bpm > LIMITS.bpmWarn) raise('warning', 'ELEVATED_HR', `Elevated heart rate: ${r.bpm} bpm`);

  if (r.temp_c == null) raise('warning', 'NO_TEMPERATURE', 'Temperature sensor without reading');
  else if (r.temp_c >= LIMITS.tempHigh) raise('alert', 'FEVER', `Fever: ${r.temp_c.toFixed(1)} °C`);
  else if (r.temp_c < LIMITS.tempLow) raise('alert', 'HYPOTHERMIA', `Hypothermia: ${r.temp_c.toFixed(1)} °C`);
  else if (r.temp_c >= LIMITS.tempWarn) raise('warning', 'LOW_GRADE_FEVER', `Low-grade fever: ${r.temp_c.toFixed(1)} °C`);

  if (r.alerts?.includes('FALL')) raise('alert', 'FALL', 'Possible fall detected');

  return { level, reasons, alertCodes };
}

/** Validates the JSON published by the ESP32; returns null for invalid messages. */
export function parseReading(payload, receivedAt) {
  let r;
  try {
    r = JSON.parse(payload);
  } catch {
    return null;
  }
  if (typeof r?.bpm !== 'number' || r.bpm < 20 || r.bpm > 250) return null;
  if (r.temp_c != null && (r.temp_c < 25 || r.temp_c > 45)) return null;

  const age = Number.isFinite(r.age_s) && r.age_s >= 0 ? r.age_s : 0;
  return {
    ...r,
    capturedAt: receivedAt - age * 1000,
    live: age <= LIVE_MAX_AGE_S,
    ...assessReading(r),
  };
}
