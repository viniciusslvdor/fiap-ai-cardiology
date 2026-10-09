import { useContext } from 'react';
import { AppointmentsContext } from '../contexts/AppointmentsContext.jsx';

export function useAppointments() {
  const context = useContext(AppointmentsContext);
  if (!context) throw new Error('useAppointments must be used inside <AppointmentsProvider>');
  return context;
}
