import { useState } from 'react';
import Badge from '../../components/Badge/Badge.jsx';
import Card from '../../components/Card/Card.jsx';
import EmptyState from '../../components/EmptyState/EmptyState.jsx';
import Icon from '../../components/Icon.jsx';
import LineChart from '../../components/LineChart/LineChart.jsx';
import StatCard from '../../components/StatCard/StatCard.jsx';
import { useVitalsStream } from '../../hooks/useVitalsStream.js';
import { LIMITS, heartRateLevel, temperatureLevel } from '../../services/vitals.js';
import styles from './Monitoring.module.css';

const STALE_MS = 30000;
const RANGES = [
  { label: '1 min', ms: 60 * 1000 },
  { label: '5 min', ms: 5 * 60 * 1000 },
  { label: '15 min', ms: 15 * 60 * 1000 },
];
const TONE = { alert: 'danger', warning: 'warning', normal: 'primary' };
const BANNER = {
  alert: { title: 'Alert', icon: 'alert' },
  warning: { title: 'Attention', icon: 'alert' },
  normal: { title: 'Vital signs within limits', icon: 'check' },
  nodata: { title: 'No live data', icon: 'clock' },
};

const clock = (ms) => new Date(ms).toLocaleTimeString('en-GB');

function duration(seconds) {
  if (seconds < 60) return `${seconds} s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min`;
  return `${Math.floor(seconds / 3600)} h ${Math.floor((seconds % 3600) / 60)} min`;
}

export default function Monitoring() {
  const { connection, deviceStatus, readings, latest, events, now } = useVitalsStream();
  const [range, setRange] = useState(RANGES[1]);

  const stale = !latest || now - latest.capturedAt > STALE_MS;
  const level = stale ? 'nodata' : latest.level;
  const banner = BANNER[level];
  const start = now - range.ms;

  const bpmPoints = readings.map((r) => ({ x: r.capturedAt, y: r.bpm }));
  const tempPoints = readings.filter((r) => r.temp_c != null).map((r) => ({ x: r.capturedAt, y: r.temp_c }));

  return (
    <div className={styles.page}>
      <div className={`${styles.banner} ${styles[level]}`}>
        <Icon name={banner.icon} size={22} />
        <div>
          <strong>{banner.title}</strong>
          {level === 'nodata' ? (
            <span>
              {latest
                ? `Last reading at ${clock(latest.capturedAt)}.`
                : 'Waiting for the wearable. Start the ESP32 simulation to see live data.'}
            </span>
          ) : (
            <span>{latest.reasons.length ? latest.reasons.join(' · ') : 'No abnormal values in the last reading.'}</span>
          )}
        </div>
      </div>

      <div className={styles.meta}>
        <span>
          Patient <strong>{latest?.patient ?? 'P001'}</strong> · {latest?.device ?? 'cardioia-wearable-01'}
        </span>
        <div className={styles.controls}>
          <div className={styles.ranges} role="group" aria-label="Chart period">
            {RANGES.map((r) => (
              <button
                key={r.label}
                type="button"
                className={r === range ? styles.rangeActive : undefined}
                onClick={() => setRange(r)}
              >
                {r.label}
              </button>
            ))}
          </div>
          <span className={`${styles.pill} ${styles[connection]}`}>
            <span className={styles.dot} />
            Broker {connection}
          </span>
        </div>
      </div>

      <div className={styles.cards}>
        <StatCard
          title="Heart rate"
          value={latest ? <>{latest.bpm} <small>bpm</small></> : '—'}
          description={latest ? (latest.bpm_source === 'button' ? 'pulse button' : 'simulated (potentiometer)') : 'no data'}
          icon="activity"
          tone={latest && !stale ? TONE[heartRateLevel(latest.bpm)] : 'primary'}
        />
        <StatCard
          title="Temperature"
          value={latest?.temp_c != null ? <>{latest.temp_c.toFixed(1)} <small>°C</small></> : '—'}
          description={latest?.humidity != null ? `humidity ${latest.humidity.toFixed(0)}%` : 'no data'}
          icon="thermometer"
          tone={latest && !stale ? TONE[temperatureLevel(latest.temp_c)] : 'primary'}
        />
        <StatCard
          title="Movement"
          value={latest ? (latest.moving ? 'Moving' : 'Still') : '—'}
          description={latest ? (latest.moving ? 'activity in the last 2 s' : `for ${duration(latest.still_s)}`) : 'no data'}
          icon="move"
          tone={latest?.alerts?.includes('FALL') && !stale ? 'danger' : 'info'}
        />
        <StatCard
          title="Device"
          value={deviceStatus === 'online' ? 'Online' : deviceStatus === 'offline' ? 'Offline' : '—'}
          description={
            latest
              ? `last reading ${duration(Math.max(0, Math.round((now - latest.capturedAt) / 1000)))} ago`
              : 'waiting for the wearable'
          }
          icon="wifi"
          tone={deviceStatus === 'offline' ? 'danger' : 'info'}
        />
      </div>

      <div className={styles.charts}>
        <Card title={`Heart rate · last ${range.label}`}>
          <LineChart
            points={bpmPoints}
            yMin={40}
            yMax={200}
            unit="bpm"
            start={start}
            end={now}
            limits={[
              { value: LIMITS.bpmHigh, label: `${LIMITS.bpmHigh} bpm` },
              { value: LIMITS.bpmLow, label: `${LIMITS.bpmLow} bpm` },
            ]}
          />
        </Card>
        <Card title={`Temperature · last ${range.label}`}>
          <LineChart
            points={tempPoints}
            yMin={34}
            yMax={42}
            unit="°C"
            start={start}
            end={now}
            color="#ea580c"
            limits={[{ value: LIMITS.tempHigh, label: `${LIMITS.tempHigh} °C` }]}
          />
        </Card>
      </div>

      <Card title="Recent alerts" noPadding>
        {events.length === 0 ? (
          <EmptyState title="No alerts" description="Alerts detected in the readings will appear here." />
        ) : (
          <ul className={styles.events}>
            {events.map((e) => (
              <li key={e.id}>
                <div className={styles.time}>
                  <strong>{clock(e.capturedAt).slice(0, 5)}</strong>
                  <span>{clock(e.capturedAt).slice(6)}s</span>
                </div>
                <div className={styles.eventInfo}>
                  <strong>{e.reasons.join(' · ')}</strong>
                  <span>
                    {e.patient} · {e.bpm} bpm · {e.temp_c != null ? `${e.temp_c.toFixed(1)} °C` : 'no temperature'}
                    {!e.live && ' · recorded while offline'}
                  </span>
                </div>
                <Badge value="high" />
              </li>
            ))}
          </ul>
        )}
      </Card>

      <p className={styles.caption}>
        Simulated wearable (ESP32) publishing to {`broker.hivemq.com`} over MQTT. Limits: heart rate above{' '}
        {LIMITS.bpmHigh} or below {LIMITS.bpmLow} bpm, temperature from {LIMITS.tempHigh} °C or below {LIMITS.tempLow} °C.
      </p>
    </div>
  );
}
