import styles from './Loading.module.css';

export default function Loading({ text = 'Loading...', fullScreen = false }) {
  return (
    <div className={fullScreen ? `${styles.wrapper} ${styles.fullscreen}` : styles.wrapper} role="status">
      <span className={styles.spinner} />
      <span className={styles.text}>{text}</span>
    </div>
  );
}
