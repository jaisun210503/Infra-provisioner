import { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const userData = await authService.getMe();
        setUser(userData);
        localStorage.setItem('user', JSON.stringify(userData));
      } catch (error) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  };

  const login = async (username, password) => {
    try {
      console.log('[AuthContext] Login attempt for:', username);

      const data = await authService.login(username, password);
      console.log('[AuthContext] Login successful, fetching user data...');

      const userData = await authService.getMe();
      console.log('[AuthContext] User data received:', {
        id: userData.id,
        username: userData.username,
        is_admin: userData.is_admin
      });

      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));
      return userData;

    } catch (error) {
      console.error('[AuthContext] Login failed:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        message: error.response?.data?.detail || error.message,
        fullError: error
      });
      throw error;
    }
  };

  const register = async (email, username, password) => {
    const userData = await authService.register(email, username, password);
    return userData;
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
