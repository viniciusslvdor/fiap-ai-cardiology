import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth.js';
import Icon from '../Icon.jsx';
import styles from './Layout.module.css';

const MENU = [
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/patients', label: 'Patients', icon: 'users' },
  { to: '/appointments', label: 'Appointments', icon: 'calendar' },
];

/** Structure of the internal pages: sidebar + header + route content (<Outlet />). */
export default function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false); // used on mobile only

  // Close the side menu (mobile) whenever the route changes.
  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  const currentPage = MENU.find((item) => location.pathname.startsWith(item.to))?.label ?? 'CardioIA';
  const initials = user?.name
    .split(' ')
    .map((part) => part[0])
    .slice(0, 2)
    .join('');

  return (
    <div className={styles.app}>
      <aside className={`${styles.sidebar} ${menuOpen ? styles.sidebarOpen : ''}`}>
        <div className={styles.brand}>
          <span className={styles.logo}>
            <Icon name="heart" size={18} />
          </span>
          <span>
            CardioIA <small>Phase 2</small>
          </span>
          <button className={styles.close} onClick={() => setMenuOpen(false)} aria-label="Close menu">
            <Icon name="close" />
          </button>
        </div>

        <nav className={styles.nav}>
          {MENU.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
            >
              <Icon name={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <p className={styles.footer}>Academic project · simulated data</p>
      </aside>

      {menuOpen && <div className={styles.overlay} onClick={() => setMenuOpen(false)} />}

      <div className={styles.main}>
        <header className={styles.header}>
          <button className={styles.hamburger} onClick={() => setMenuOpen(true)} aria-label="Open menu">
            <Icon name="menu" />
          </button>
          <h1 className={styles.pageTitle}>{currentPage}</h1>

          <div className={styles.user}>
            <span className={styles.avatar}>{initials}</span>
            <span className={styles.userInfo}>
              <strong>{user?.name}</strong>
              <small>{user?.role}</small>
            </span>
            <button className="btn btn-ghost" onClick={logout} title="Log out">
              <Icon name="logout" size={18} />
              <span className={styles.logoutText}>Log out</span>
            </button>
          </div>
        </header>

        <main className={styles.content}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
