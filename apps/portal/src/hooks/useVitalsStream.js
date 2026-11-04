import mqtt from 'mqtt';
import { useEffect, useReducer, useState } from 'react';
import { MQTT_URL, TOPIC_ROOT, WINDOW_MS, parseReading } from '../services/vitals.js';

const MAX_EVENTS = 20;

const initialState = {
  connection: 'connecting', // connecting | connected | error
  deviceStatus: null, // online | offline | null
  readings: [], // last 15 min, sorted by capture time
  latest: null, // last live reading
  events: [], // alert history
  lastAlertKey: '',
};

function reducer(state, action) {
  switch (action.type) {
    case 'connection':
      return { ...state, connection: action.value };
    case 'status':
      return { ...state, deviceStatus: action.value };
    case 'reading': {
      const r = action.reading;
      const readings = [...state.readings.filter((p) => p.capturedAt >= action.receivedAt - WINDOW_MS), r].sort(
        (a, b) => a.capturedAt - b.capturedAt,
      );

      let { events, lastAlertKey } = state;
      const key = r.alertCodes.join('|');
      if (key && key !== lastAlertKey) {
        const event = { id: `${r.device}-${r.seq}-${r.capturedAt}`, ...r };
        events = [event, ...events].slice(0, MAX_EVENTS);
      }
      if (r.live || key) lastAlertKey = key;

      return { ...state, readings, events, lastAlertKey, latest: r.live ? r : state.latest };
    }
    default:
      return state;
  }
}

/** Subscribes to the wearable topics on the MQTT broker (WebSocket) and keeps the last 15 minutes. */
export function useVitalsStream() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [now, setNow] = useState(Date.now());

  useEffect(() => {
    const client = mqtt.connect(MQTT_URL, {
      clientId: `cardioia-portal-${Math.random().toString(16).slice(2, 10)}`,
      reconnectPeriod: 5000,
      connectTimeout: 10000,
    });

    client.on('connect', () => {
      dispatch({ type: 'connection', value: 'connected' });
      client.subscribe([`${TOPIC_ROOT}/+/vitals`, `${TOPIC_ROOT}/+/status`]);
    });
    client.on('reconnect', () => dispatch({ type: 'connection', value: 'connecting' }));
    client.on('error', () => dispatch({ type: 'connection', value: 'error' }));
    client.on('message', (topic, payload) => {
      const text = payload.toString();
      if (topic.endsWith('/status')) {
        dispatch({ type: 'status', value: text.trim() || null });
        return;
      }
      const receivedAt = Date.now();
      const reading = parseReading(text, receivedAt);
      if (reading) dispatch({ type: 'reading', reading, receivedAt });
    });

    return () => client.end(true);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  return { ...state, now };
}
