'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Mail, Lock, Briefcase, AlertCircle, CheckCircle, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import api from '@/lib/api';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

export default function LoginPage() {
  const { login, user } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailVerified, setEmailVerified] = useState<boolean | null>(null);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (user) {
      checkVerification();
    }
  }, [user]);

  const checkVerification = async () => {
    try {
      const res = await api.get('/auth/check-verification/');
      setEmailVerified(res.data.is_verified);
    } catch {
      setEmailVerified(null);
    }
  };

  const resendVerification = async () => {
    setResendLoading(true);
    try {
      await api.post('/auth/send-verification/', { email: user?.email });
      setResendSuccess(true);
    } catch {
      setError('Ошибка отправки письма');
    } finally {
      setResendLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(username, password);
      router.push('/jobs');
    } catch {
      setError('Неверное имя пользователя или пароль');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
      <div className="w-full max-w-md">
        <div className="card p-6 sm:p-8">
          <div className="text-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-accent-primary to-accent-cyan flex items-center justify-center mx-auto mb-4 shadow-lg shadow-accent-primary/20">
              <Briefcase size={26} className="text-white" />
            </div>
            <h1 className="font-heading font-bold text-2xl mb-1.5 text-text-primary">Добро пожаловать</h1>
            <p className="text-sm text-text-muted">Войдите, чтобы продолжить поиск работы</p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-3.5">
            {error && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-500 text-sm flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-[10px] font-bold">!</span>
                </div>
                {error}
              </div>
            )}

            <Input
              label="Имя пользователя"
              placeholder="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              icon={<Mail size={16} />}
              required
            />

            <div className="relative">
              <Input
                label="Пароль"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                icon={<Lock size={16} />}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-[38px] text-text-muted hover:text-text-primary transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            <div className="flex justify-end">
              <Link href="/auth/forgot-password" className="text-xs font-medium text-accent-primary hover:text-accent-primary-hover transition-colors">
                Забыли пароль?
              </Link>
            </div>

            <Button type="submit" loading={loading} className="w-full h-11">
              Войти
            </Button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border-default"></div>
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-3 bg-card text-text-muted">или</span>
            </div>
          </div>

          <button
            type="button"
            onClick={() => window.location.href = `${process.env.NEXT_PUBLIC_API_URL}/auth/google/`}
            className="w-full h-11 rounded-xl border border-border-default bg-surface-default hover:bg-surface-hover transition-all duration-200 flex items-center justify-center gap-3 text-text-secondary hover:text-text-primary font-medium text-sm"
          >
            <svg viewBox="0 0 24 24" width="20" height="20">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Войти через Google
          </button>

          <p className="text-center text-sm text-text-muted mt-4">
            Нет аккаунта?{' '}
            <Link href="/auth/register" className="text-accent-primary hover:text-accent-primary-hover transition-colors font-semibold">
              Зарегистрироваться
            </Link>
          </p>
        </div>

        {user && emailVerified === false && (
          <div className="mt-4 p-4 rounded-xl border border-yellow-500/30 bg-yellow-500/5">
            <div className="flex items-start gap-3">
              <AlertCircle size={20} className="text-yellow-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-yellow-400 font-medium">Email не верифицирован</p>
                <p className="text-xs text-text-muted mt-1">
                  Проверьте почту {user.email} или запросите новое письмо
                </p>
                {resendSuccess ? (
                  <div className="flex items-center gap-2 mt-2">
                    <CheckCircle size={14} className="text-accent-primary" />
                    <span className="text-xs text-accent-primary">Письмо отправлено!</span>
                  </div>
                ) : (
                  <Button
                    onClick={resendVerification}
                    loading={resendLoading}
                    variant="secondary"
                    size="sm"
                    className="mt-2"
                  >
                    Отправить повторно
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
