import styles from './Badge.module.css';

const VARIANTS = {
  high: 'danger',
  moderate: 'warning',
  low: 'success',
  'Under follow-up': 'info',
  'Awaiting tests': 'warning',
  Discharged: 'success',
};

const LABELS = { high: 'High', moderate: 'Moderate', low: 'Low' };

/** Colored tag for risk ("high", "moderate", "low") or patient status. */
export default function Badge({ value }) {
  const variant = VARIANTS[value] ?? 'neutral';
  return <span className={`${styles.badge} ${styles[variant]}`}>{LABELS[value] ?? value}</span>;
}
