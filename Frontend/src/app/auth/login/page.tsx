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

          <p className="text-center text-sm text-text-muted">
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
