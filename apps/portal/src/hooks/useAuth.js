import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext.jsx';

/** Shortcut to consume AuthContext, with a clear error message if used outside the Provider. */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>');
  return context;
}
