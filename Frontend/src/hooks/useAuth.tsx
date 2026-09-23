'use client';

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import api, { saveTokens, removeTokens } from '@/lib/api';
import type { User } from '@/types';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: { username: string; email: string; password: string; role: string; phone?: string }) => Promise<void>;
  logout: () => void;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const fetchUser = useCallback(async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }
      const res = await api.get('/users/me/');
      setUser(res.data);
    } catch (err) {
      const axiosError = err as { response?: { status?: number } };
      if (axiosError.response?.status === 401) {
        removeTokens();
      }
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = async (username: string, password: string) => {
    const res = await api.post('/auth/login/', { username, password });
    saveTokens(res.data.access, res.data.refresh);
    await fetchUser();
  };

  const register = async (data: { username: string; email: string; password: string; role: string; phone?: string; companyName?: string }) => {
    await api.post('/auth/register/', {
      username: data.username,
      email: data.email,
      password: data.password,
      role: data.role,
      phone: data.phone,
      company_name: data.companyName,
    });
    await login(data.username, data.password);
  };

  const logout = () => {
    removeTokens();
    setUser(null);
    router.push('/');
  };

  const updateUser = (updated: User) => setUser(updated);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
