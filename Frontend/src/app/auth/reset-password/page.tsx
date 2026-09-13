'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Lock, Briefcase, ArrowLeft, CheckCircle } from 'lucide-react';
import api from '@/lib/api';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }

    if (password.length < 6) {
      setError('Пароль должен содержать минимум 6 символов');
      return;
    }

    if (!token) {
      setError('Токен не найден. Запросите новую ссылку.');
      return;
    }

    setLoading(true);
    try {
      await api.post('/auth/password-reset/confirm/', { token, new_password: password });
      setSuccess(true);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Ошибка сброса пароля');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
        <div className="w-full max-w-md">
          <div className="card p-8 text-center">
            <div className="w-14 h-14 rounded-full bg-accent-primary/10 flex items-center justify-center mx-auto mb-4">
              <CheckCircle size={28} className="text-accent-primary" />
            </div>
            <h1 className="font-heading font-semibold text-2xl mb-2">Пароль изменён</h1>
            <p className="text-sm text-text-muted mb-6">
              Теперь вы можете войти с новым паролем.
            </p>
            <Button onClick={() => router.push('/auth/login')} className="w-full">
              Войти
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
        <div className="w-full max-w-md">
          <div className="card p-8 text-center">
            <h1 className="font-heading font-semibold text-2xl mb-2">Неверная ссылка</h1>
            <p className="text-sm text-text-muted mb-6">Ссылка для сброса пароля недействительна.</p>
            <Link href="/auth/forgot-password" className="text-accent-primary hover:text-accent-primary-hover transition-colors font-medium text-sm">
              Запросить новую ссылку
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
      <div className="w-full max-w-md">
        <div className="card p-8">
          <div className="text-center mb-8">
            <div className="w-12 h-12 rounded-lg bg-accent-primary flex items-center justify-center mx-auto mb-4">
              <Briefcase size={24} className="text-text-on-accent" />
            </div>
            <h1 className="font-heading font-semibold text-2xl mb-2">Новый пароль</h1>
            <p className="text-sm text-text-muted">Введите новый пароль</p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
                {error}
              </div>
            )}

            <Input
              label="Новый пароль"
              type="password"
              placeholder="Минимум 6 символов"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock size={16} />}
              required
              minLength={6}
            />

            <Input
              label="Подтвердите пароль"
              type="password"
              placeholder="Повторите пароль"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              icon={<Lock size={16} />}
              required
              minLength={6}
            />

            <Button type="submit" loading={loading} className="w-full mt-2">
              Изменить пароль
            </Button>
          </form>

          <p className="text-center text-sm text-text-muted mt-6">
            <Link href="/auth/login" className="text-accent-primary hover:text-accent-primary-hover transition-colors font-medium inline-flex items-center gap-1.5">
              <ArrowLeft size={14} />
              Вернуться к входу
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
