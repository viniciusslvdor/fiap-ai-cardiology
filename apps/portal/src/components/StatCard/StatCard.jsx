import Icon from '../Icon.jsx';
import styles from './StatCard.module.css';

/** Dashboard metric card. `tone` sets the icon color: primary | info | warning | danger */
export default function StatCard({ title, value, description, icon, tone = 'primary' }) {
  return (
    <article className={styles.card}>
      <div className={`${styles.icon} ${styles[tone]}`}>
        <Icon name={icon} size={22} />
      </div>
      <div>
        <p className={styles.title}>{title}</p>
        <p className={styles.value}>{value}</p>
        {description && <p className={styles.description}>{description}</p>}
      </div>
    </article>
  );
}
