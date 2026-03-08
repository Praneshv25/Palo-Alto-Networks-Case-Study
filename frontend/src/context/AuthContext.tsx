import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { User } from '../types/report';
import { signup as apiSignup } from '../lib/api';

interface SignupParams {
  username: string;
  password: string;
  neighborhood: string;
  lat?: number | null;
  lng?: number | null;
}

interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  signup: (params: SignupParams) => Promise<void>;
  updateUser: (updates: Partial<User>) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem('guardian_token');
    if (!saved) {
      setLoading(false);
      return;
    }
    fetch('http://127.0.0.1:5001/api/me', {
      headers: { Authorization: `Bearer ${saved}` },
    })
      .then(r => (r.ok ? r.json() : Promise.reject()))
      .then((u: User) => {
        setUser(u);
        setToken(saved);
      })
      .catch(() => {
        localStorage.removeItem('guardian_token');
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const res = await fetch('http://127.0.0.1:5001/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || 'Login failed');
    }
    const data = await res.json();
    localStorage.setItem('guardian_token', data.token);
    setToken(data.token);
    setUser(data.user);
  };

  const signup = async (params: SignupParams) => {
    const data = await apiSignup(params);
    localStorage.setItem('guardian_token', data.token);
    setToken(data.token);
    setUser(data.user);
  };

  const updateUser = (updates: Partial<User>) => {
    setUser(prev => (prev ? { ...prev, ...updates } : prev));
  };

  const logout = () => {
    if (token) {
      fetch('http://127.0.0.1:5001/api/logout', {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      }).catch(() => {});
    }
    localStorage.removeItem('guardian_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, updateUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
