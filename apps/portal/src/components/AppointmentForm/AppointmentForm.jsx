import { useEffect, useState } from 'react';
import { useAppointments } from '../../hooks/useAppointments.js';
import { todayISO } from '../../utils/dates.js';
import Icon from '../Icon.jsx';
import styles from './AppointmentForm.module.css';

const EMPTY_FORM = { patientId: '', date: '', time: '', doctor: '', notes: '' };
const MAX_NOTES = 200;

/** Form validation rules. Returns { field: message } for each error found. */
function validate(form, appointments) {
  const errors = {};
  if (!form.patientId) errors.patientId = 'Select the patient.';
  if (!form.doctor) errors.doctor = 'Select the doctor.';
  if (!form.date) errors.date = 'Enter the date.';
  else if (form.date < todayISO()) errors.date = 'The date cannot be in the past.';
  if (!form.time) errors.time = 'Enter the time.';
  else if (form.time < '07:00' || form.time > '19:00') errors.time = 'Office hours are 07:00 to 19:00.';
  if (form.notes.length > MAX_NOTES) errors.notes = `Maximum of ${MAX_NOTES} characters.`;

  const conflict = appointments.some(
    (appt) => appt.doctor === form.doctor && appt.date === form.date && appt.time === form.time,
  );
  if (!errors.time && conflict) errors.time = 'This doctor already has an appointment at this time.';
  return errors;
}

export default function AppointmentForm({ patients, doctors }) {
  const { appointments, add } = useAppointments();
  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState('');

  // Hide the success message after 4 seconds.
  useEffect(() => {
    if (!success) return undefined;
    const timer = setTimeout(() => setSuccess(''), 4000);
    return () => clearTimeout(timer);
  }, [success]);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const newErrors = validate(form, appointments);
    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) {
      setSuccess('');
      return;
    }

    const patient = patients.find((p) => p.id === Number(form.patientId));
    add({
      patientId: patient.id,
      patientName: patient.name,
      date: form.date,
      time: form.time,
      doctor: form.doctor,
      notes: form.notes.trim(),
    });
    setSuccess(`Appointment for ${patient.name} booked successfully.`);
    setForm(EMPTY_FORM);
  }

  const field = (name, label, input) => (
    <label className={styles.field}>
      <span>{label}</span>
      {input}
      {errors[name] && <small className={styles.error}>{errors[name]}</small>}
    </label>
  );

  return (
    <form className={styles.form} onSubmit={handleSubmit} noValidate>
      {success && (
        <p className={styles.success} role="status">
          <Icon name="check" size={18} /> {success}
        </p>
      )}

      {field(
        'patientId',
        'Patient',
        <select className="input" name="patientId" value={form.patientId} onChange={handleChange} aria-invalid={Boolean(errors.patientId)}>
          <option value="">Select...</option>
          {patients.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>,
      )}

      <div className={styles.row}>
        {field(
          'date',
          'Date',
          <input className="input" type="date" name="date" min={todayISO()} value={form.date} onChange={handleChange} aria-invalid={Boolean(errors.date)} />,
        )}
        {field(
          'time',
          'Time',
          <input className="input" type="time" name="time" min="07:00" max="19:00" step="900" value={form.time} onChange={handleChange} aria-invalid={Boolean(errors.time)} />,
        )}
      </div>

      {field(
        'doctor',
        'Doctor',
        <select className="input" name="doctor" value={form.doctor} onChange={handleChange} aria-invalid={Boolean(errors.doctor)}>
          <option value="">Select...</option>
          {doctors.map((d) => (
            <option key={d.id} value={d.name}>
              {d.name} · {d.specialty}
            </option>
          ))}
        </select>,
      )}

      {field(
        'notes',
        `Notes (${form.notes.length}/${MAX_NOTES})`,
        <textarea className="input" name="notes" rows={3} placeholder="Optional" value={form.notes} onChange={handleChange} aria-invalid={Boolean(errors.notes)} />,
      )}

      <button className="btn btn-primary" type="submit">
        <Icon name="calendar" size={18} /> Book appointment
      </button>
    </form>
  );
}
