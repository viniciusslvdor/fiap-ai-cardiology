import { useState } from 'react';
import AppointmentForm from '../../components/AppointmentForm/AppointmentForm.jsx';
import Card from '../../components/Card/Card.jsx';
import EmptyState from '../../components/EmptyState/EmptyState.jsx';
import Icon from '../../components/Icon.jsx';
import Loading from '../../components/Loading/Loading.jsx';
import { useAppointments } from '../../hooks/useAppointments.js';
import { useFakeApi } from '../../hooks/useFakeApi.js';
import { getDoctors, getPatients } from '../../services/api.js';
import { formatDate, todayISO } from '../../utils/dates.js';
import styles from './Appointments.module.css';

const FILTERS = [
  { value: 'upcoming', label: 'Upcoming' },
  { value: 'today', label: 'Today' },
  { value: 'all', label: 'All' },
];

export default function Appointments() {
  const { appointments, cancel, reset } = useAppointments();
  const { data: patients, loading: loadingPatients } = useFakeApi(getPatients);
  const { data: doctors, loading: loadingDoctors } = useFakeApi(getDoctors);
  const [filter, setFilter] = useState('upcoming');

  const today = todayISO();
  const list = appointments
    .filter((appt) => (filter === 'today' ? appt.date === today : filter === 'upcoming' ? appt.date >= today : true))
    .sort((a, b) => `${a.date} ${a.time}`.localeCompare(`${b.date} ${b.time}`));

  const tabs = (
    <div className={styles.tabs} role="tablist">
      {FILTERS.map((f) => (
        <button
          key={f.value}
          role="tab"
          aria-selected={filter === f.value}
          className={filter === f.value ? `${styles.tab} ${styles.activeTab}` : styles.tab}
          onClick={() => setFilter(f.value)}
        >
          {f.label}
        </button>
      ))}
    </div>
  );

  return (
    <div className={styles.grid}>
      <Card title="New appointment">
        {loadingPatients || loadingDoctors ? (
          <Loading text="Loading form..." />
        ) : (
          <AppointmentForm patients={patients} doctors={doctors} />
        )}
      </Card>

      <Card title={`Appointments (${list.length})`} actions={tabs} noPadding>
        {list.length === 0 ? (
          <EmptyState
            title="No appointments found"
            description={filter === 'today' ? 'There are no appointments today.' : 'Fill in the form to book one.'}
          >
            {appointments.length === 0 && (
              <button className="btn btn-ghost" onClick={reset}>
                Restore sample data
              </button>
            )}
          </EmptyState>
        ) : (
          <ul className={styles.list}>
            {list.map((appt) => (
              <li key={appt.id} className={appt.date < today ? styles.past : undefined}>
                <div className={styles.when}>
                  <strong>{appt.date === today ? 'Today' : formatDate(appt.date)}</strong>
                  <span>{appt.time}</span>
                </div>
                <div className={styles.info}>
                  <strong>{appt.patientName}</strong>
                  <span>{appt.doctor}</span>
                  {appt.notes && <em>{appt.notes}</em>}
                </div>
                <button
                  className={styles.cancel}
                  onClick={() => cancel(appt.id)}
                  title="Cancel appointment"
                  aria-label={`Cancel appointment for ${appt.patientName}`}
                >
                  <Icon name="trash" size={18} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
