import styles from './LineChart.module.css';

const W = 640;
const H = 240;
const PAD = { top: 12, right: 16, bottom: 28, left: 40 };
const GAP_MS = 15000; // no reading for 15 s -> break the line

const timeLabel = (ms, withSeconds) =>
  new Date(ms).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: withSeconds ? '2-digit' : undefined });

/** Time series chart in SVG. points: [{ x: ms, y }], limits: [{ value, label }] */
export default function LineChart({ points, yMin, yMax, unit, limits = [], start, end, color = 'var(--color-primary)' }) {
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;
  const sx = (x) => PAD.left + ((x - start) / (end - start)) * plotW;
  const sy = (y) => PAD.top + (1 - (Math.min(Math.max(y, yMin), yMax) - yMin) / (yMax - yMin)) * plotH;

  const visible = points.filter((p) => p.x >= start && p.x <= end);
  let path = '';
  visible.forEach((p, i) => {
    const jump = i === 0 || p.x - visible[i - 1].x > GAP_MS;
    path += `${jump ? 'M' : 'L'}${sx(p.x).toFixed(1)},${sy(p.y).toFixed(1)}`;
  });
  const last = visible.at(-1);

  const yTicks = Array.from({ length: 5 }, (_, i) => yMin + ((yMax - yMin) * i) / 4);
  const xTicks = Array.from({ length: 6 }, (_, i) => start + ((end - start) * i) / 5);
  const withSeconds = end - start <= 5 * 60 * 1000;

  return (
    <div className={styles.wrapper}>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.chart} role="img" aria-label={`Chart in ${unit}`}>
        {yTicks.map((t) => (
          <g key={t}>
            <line x1={PAD.left} x2={W - PAD.right} y1={sy(t)} y2={sy(t)} className={styles.grid} />
            <text x={PAD.left - 8} y={sy(t)} className={styles.yLabel}>
              {Number.isInteger(t) ? t : t.toFixed(1)}
            </text>
          </g>
        ))}
        {xTicks.map((t, i) => (
          <text
            key={t}
            x={sx(t)}
            y={H - 8}
            className={styles.xLabel}
            style={{ textAnchor: i === 0 ? 'start' : i === xTicks.length - 1 ? 'end' : 'middle' }}
          >
            {timeLabel(t, withSeconds)}
          </text>
        ))}
        {limits.map((l) => (
          <g key={l.value}>
            <line x1={PAD.left} x2={W - PAD.right} y1={sy(l.value)} y2={sy(l.value)} className={styles.limit} />
            <text x={PAD.left + 6} y={sy(l.value) - 5} className={styles.limitLabel}>
              {l.label}
            </text>
          </g>
        ))}
        {path && <path d={path} className={styles.line} style={{ stroke: color }} />}
        {last && <circle cx={sx(last.x)} cy={sy(last.y)} r="4" style={{ fill: color }} />}
      </svg>
      {visible.length === 0 && <p className={styles.empty}>Waiting for readings…</p>}
    </div>
  );
}
