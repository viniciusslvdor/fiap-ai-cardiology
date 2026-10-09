import Icon from '../Icon.jsx';
import styles from './EmptyState.module.css';

export default function EmptyState({ title, description, children }) {
  return (
    <div className={styles.empty}>
      <span className={styles.icon}>
        <Icon name="inbox" size={28} />
      </span>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {children}
    </div>
  );
}
