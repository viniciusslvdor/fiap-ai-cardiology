import styles from './Card.module.css';

/** White panel with an optional title and actions on the right. */
export default function Card({ title, actions, children, noPadding = false }) {
  return (
    <section className={styles.card}>
      {(title || actions) && (
        <header className={styles.header}>
          {title && <h2>{title}</h2>}
          {actions && <div className={styles.actions}>{actions}</div>}
        </header>
      )}
      <div className={noPadding ? undefined : styles.body}>{children}</div>
    </section>
  );
}
