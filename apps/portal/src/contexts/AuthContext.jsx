import { createContext, useEffect, useState } from 'react';
import * as authService from '../services/authService.js';

const TOKEN_KEY = 'cardioia_token';
const USER_KEY = 'cardioia_user';

export const AuthContext = createContext(null);

/**
 * Holds the (simulated) authentication state and shares it with the whole app
 * through the Context API. The fake token is kept in localStorage so it survives a page refresh.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true); // true while the session is being restored

  // When the app opens, try to restore the saved session (and discard expired/invalid tokens).
  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY);
    const savedUser = localStorage.getItem(USER_KEY);
    if (savedToken && savedUser && authService.isTokenValid(savedToken)) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    } else {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
    setLoading(false);
  }, []);

  async function login(email, password) {
    const response = await authService.login(email, password); // throws if the credentials are invalid
    localStorage.setItem(TOKEN_KEY, response.token);
    localStorage.setItem(USER_KEY, JSON.stringify(response.user));
    setToken(response.token);
    setUser(response.user);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
  }

  const value = { user, token, isAuthenticated: Boolean(token), loading, login, logout };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
