import Icon from '../Icon.jsx';
import styles from './Disclaimer.module.css';

export default function Disclaimer() {
  return (
    <p className={styles.notice}>
      <Icon name="alert" size={18} />
      <span>
        <strong>Academic demo environment.</strong> All patients and data are fictitious. CardioIA is an experimental
        decision-support system and does not perform medical diagnosis.
      </span>
    </p>
  );
}
