'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Mail, Briefcase, ArrowLeft, CheckCircle } from 'lucide-react';
import api from '@/lib/api';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await api.post('/auth/password-reset/', { email });
      setSent(true);
    } catch {
      setSent(true);
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
        <div className="w-full max-w-md">
          <div className="card p-8 text-center">
            <div className="w-14 h-14 rounded-full bg-accent-primary/10 flex items-center justify-center mx-auto mb-4">
              <CheckCircle size={28} className="text-accent-primary" />
            </div>
            <h1 className="font-heading font-semibold text-2xl mb-2">Письмо отправлено</h1>
            <p className="text-sm text-text-muted mb-6">
              Если аккаунт с email <span className="font-medium text-text-primary">{email}</span> существует, вы получите письмо со ссылкой для сброса пароля.
            </p>
            <Link
              href="/auth/login"
              className="inline-flex items-center gap-2 text-sm font-medium text-accent-primary hover:text-accent-primary-hover transition-colors"
            >
              <ArrowLeft size={16} />
              Вернуться к входу
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
            <h1 className="font-heading font-semibold text-2xl mb-2">Сброс пароля</h1>
            <p className="text-sm text-text-muted">Введите email для получения ссылки сброса</p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-sm">
                {error}
              </div>
            )}

            <Input
              label="Email"
              type="email"
              placeholder="email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              icon={<Mail size={16} />}
              required
            />

            <Button type="submit" loading={loading} className="w-full mt-2">
              Отправить ссылку
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
