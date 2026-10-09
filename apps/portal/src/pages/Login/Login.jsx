import { useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import Icon from '../../components/Icon.jsx';
import { useAuth } from '../../hooks/useAuth.js';
import { DEMO_CREDENTIALS } from '../../services/authService.js';
import styles from './Login.module.css';

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validate({ email, password }) {
  const errors = {};
  if (!email.trim()) errors.email = 'Enter your email.';
  else if (!EMAIL_REGEX.test(email.trim())) errors.email = 'Invalid email format.';
  if (!password) errors.password = 'Enter your password.';
  else if (password.length < 6) errors.password = 'The password must have at least 6 characters.';
  return errors;
}

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const location = useLocation();

  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [loginError, setLoginError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // After login (or if a session already exists), go back to the page the user tried to open.
  if (isAuthenticated) return <Navigate to={location.state?.from ?? '/dashboard'} replace />;

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: undefined }));
    setLoginError('');
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const newErrors = validate(form);
    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;

    setSubmitting(true);
    try {
      await login(form.email, form.password); // once the context updates, the <Navigate> above redirects
    } catch (err) {
      setLoginError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className={styles.page}>
      <section className={styles.brandPanel}>
        <span className={styles.logo}>
          <Icon name="heart" size={28} />
        </span>
        <h1>CardioIA</h1>
        <p>Academic decision-support portal for cardiology. Phase 2: Automated Diagnosis.</p>
        <ul>
          <li>
            <Icon name="check" size={16} /> Simulated patients and risk levels
          </li>
          <li>
            <Icon name="check" size={16} /> Appointment booking
          </li>
          <li>
            <Icon name="check" size={16} /> Dashboard with metrics
          </li>
        </ul>
      </section>

      <section className={styles.formPanel}>
        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <h2>Sign in</h2>
          <p className={styles.subtitle}>Use the demo credentials to access the portal.</p>

          {loginError && (
            <p className={styles.formError} role="alert">
              {loginError}
            </p>
          )}

          <label className={styles.field}>
            <span>Email</span>
            <input
              className="input"
              type="email"
              name="email"
              autoComplete="username"
              placeholder="you@email.com"
              value={form.email}
              onChange={handleChange}
              aria-invalid={Boolean(errors.email)}
            />
            {errors.email && <small className={styles.error}>{errors.email}</small>}
          </label>

          <label className={styles.field}>
            <span>Password</span>
            <input
              className="input"
              type="password"
              name="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={form.password}
              onChange={handleChange}
              aria-invalid={Boolean(errors.password)}
            />
            {errors.password && <small className={styles.error}>{errors.password}</small>}
          </label>

          <button className={`btn btn-primary ${styles.submit}`} type="submit" disabled={submitting}>
            {submitting ? 'Signing in...' : 'Sign in'}
          </button>

          <div className={styles.demo}>
            <p>
              <strong>Demo credentials</strong>
              <br />
              {DEMO_CREDENTIALS.email} · {DEMO_CREDENTIALS.password}
            </p>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setForm({ ...DEMO_CREDENTIALS });
                setErrors({});
                setLoginError('');
              }}
            >
              Fill in
            </button>
          </div>

          <p className={styles.note}>Simulated authentication (fake JWT in localStorage). This is not real security.</p>
        </form>
      </section>
    </div>
  );
}
