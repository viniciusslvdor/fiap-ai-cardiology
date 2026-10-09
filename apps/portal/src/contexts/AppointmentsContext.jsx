import { createContext, useEffect, useReducer } from 'react';
import seedAppointments from '../data/appointments.json';
import { shiftDays } from '../utils/dates.js';

const STORAGE_KEY = 'cardioia_appointments';

export const AppointmentsContext = createContext(null);

/**
 * Reducer: holds ALL the rules for changing the appointment list.
 * Each action describes "what happened"; the reducer returns the new state.
 */
export function appointmentsReducer(state, action) {
  switch (action.type) {
    case 'ADD':
      return [...state, action.payload];
    case 'CANCEL':
      return state.filter((appt) => appt.id !== action.payload);
    case 'RESET':
      return createInitialState();
    default:
      throw new Error(`Unknown action: ${action.type}`);
  }
}

/** Seed appointments use dates relative to today, so the dashboard always has "appointments today". */
function createInitialState() {
  return seedAppointments.map(({ daysFromToday, ...appt }) => ({ ...appt, date: shiftDays(daysFromToday) }));
}

function loadState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : createInitialState();
  } catch {
    return createInitialState();
  }
}

export function AppointmentsProvider({ children }) {
  // The 3rd argument (init function) runs only once, on mount.
  const [appointments, dispatch] = useReducer(appointmentsReducer, undefined, loadState);

  // Persist to localStorage whenever the list changes.
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(appointments));
  }, [appointments]);

  const value = {
    appointments,
    add: (appointment) => dispatch({ type: 'ADD', payload: { ...appointment, id: crypto.randomUUID() } }),
    cancel: (id) => dispatch({ type: 'CANCEL', payload: id }),
    reset: () => dispatch({ type: 'RESET' }),
  };
  return <AppointmentsContext.Provider value={value}>{children}</AppointmentsContext.Provider>;
}
