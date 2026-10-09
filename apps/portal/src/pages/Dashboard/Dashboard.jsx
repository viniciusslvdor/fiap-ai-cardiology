import { Link } from 'react-router-dom';
import Badge from '../../components/Badge/Badge.jsx';
import Card from '../../components/Card/Card.jsx';
import Disclaimer from '../../components/Disclaimer/Disclaimer.jsx';
import EmptyState from '../../components/EmptyState/EmptyState.jsx';
import Loading from '../../components/Loading/Loading.jsx';
import StatCard from '../../components/StatCard/StatCard.jsx';
import { useAppointments } from '../../hooks/useAppointments.js';
import { useFakeApi } from '../../hooks/useFakeApi.js';
import { getPatients } from '../../services/api.js';
import { formatDate, todayISO } from '../../utils/dates.js';
import styles from './Dashboard.module.css';

const RISK_LEVELS = [
  { key: 'high', label: 'High' },
  { key: 'moderate', label: 'Moderate' },
  { key: 'low', label: 'Low' },
];

export default function Dashboard() {
  const { data: patients, loading } = useFakeApi(getPatients);
  const { appointments } = useAppointments();

  if (loading) return <Loading text="Loading indicators..." />;

  // Derived metrics: computed on every render from the state (they do not need their own useState).
  const today = todayISO();
  const upcoming = appointments
    .filter((appt) => appt.date >= today)
    .sort((a, b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`));
  const appointmentsToday = upcoming.filter((appt) => appt.date === today).length;
  const riskCount = Object.fromEntries(
    RISK_LEVELS.map(({ key }) => [key, patients.filter((p) => p.risk === key).length]),
  );
  const riskByPatient = Object.fromEntries(patients.map((p) => [p.id, p.risk]));

  return (
    <div className={styles.page}>
      <Disclaimer />

      <div className={styles.cards}>
        <StatCard title="Total patients" value={patients.length} description="registered in the portal" icon="users" />
        <StatCard title="Scheduled appointments" value={upcoming.length} description="from today on" icon="calendar" tone="info" />
        <StatCard title="Appointments today" value={appointmentsToday} description={formatDate(today)} icon="clock" tone="warning" />
        <StatCard
          title="High-risk cases"
          value={riskCount.high}
          description={`${Math.round((riskCount.high / patients.length) * 100)}% of patients`}
          icon="alert"
          tone="danger"
        />
      </div>

      <div className={styles.grid}>
        <Card title="Risk distribution">
          <ul className={styles.bars}>
            {RISK_LEVELS.map(({ key, label }) => {
              const percent = (riskCount[key] / patients.length) * 100;
              return (
                <li key={key}>
                  <div className={styles.barLegend}>
                    <span>{label}</span>
                    <strong>
                      {riskCount[key]} <small>({percent.toFixed(0)}%)</small>
                    </strong>
                  </div>
                  <div className={styles.track}>
                    <div className={`${styles.bar} ${styles[key]}`} style={{ width: `${percent}%` }} />
                  </div>
                </li>
              );
            })}
          </ul>
          <p className={styles.caption}>Fictitious risk classification, for demonstration only.</p>
        </Card>

        <Card title="Upcoming appointments" actions={<Link to="/appointments">See all</Link>} noPadding>
          {upcoming.length === 0 ? (
            <EmptyState title="No upcoming appointments" description="Use the appointments page to book one." />
          ) : (
            <ul className={styles.upcoming}>
              {upcoming.slice(0, 5).map((appt) => (
                <li key={appt.id}>
                  <div className={styles.dateTime}>
                    <strong>{appt.date === today ? 'Today' : formatDate(appt.date, { month: 'short', day: 'numeric' })}</strong>
                    <span>{appt.time}</span>
                  </div>
                  <div className={styles.apptInfo}>
                    <strong>{appt.patientName}</strong>
                    <span>{appt.doctor}</span>
                  </div>
                  {riskByPatient[appt.patientId] && <Badge value={riskByPatient[appt.patientId]} />}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
