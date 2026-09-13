'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Mail, Lock, User, Phone, Briefcase, GraduationCap, Building2, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import { clsx, getErrorMessage } from '@/lib/utils';

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [role, setRole] = useState<'student' | 'employer'>('student');
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    phone: '',
    companyName: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (form.password !== form.confirmPassword) {
      setError('Пароли не совпадают');
      return;
    }

    if (form.password.length < 6) {
      setError('Пароль должен содержать минимум 6 символов');
      return;
    }

    setLoading(true);
    try {
      await register({ ...form, role });
      router.push(role === 'student' ? '/profile/student' : '/profile/employer');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const update = (field: string, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center px-4 sm:px-6 py-8 sm:py-12">
      <div className="w-full max-w-md">
        <div className="card p-6 sm:p-8">
          <div className="text-center mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-accent-primary to-accent-cyan flex items-center justify-center mx-auto mb-4 shadow-lg shadow-accent-primary/20">
              <Briefcase size={26} className="text-white" />
            </div>
            <h1 className="font-heading font-bold text-2xl mb-1.5 text-text-primary">Создать аккаунт</h1>
            <p className="text-sm text-text-muted">Присоединяйтесь к тысячам студентов</p>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-6">
            <button
              type="button"
              onClick={() => setRole('student')}
              className={clsx(
                'group p-4 rounded-xl border-2 text-center transition-all duration-200',
                role === 'student'
                  ? 'border-accent-primary bg-accent-primary/10 shadow-sm shadow-accent-primary/10'
                  : 'border-border-default hover:border-border-hover hover:bg-surface-hover'
              )}
            >
              <div className={clsx(
                'w-10 h-10 rounded-xl mx-auto mb-2.5 flex items-center justify-center transition-all',
                role === 'student'
                  ? 'bg-accent-primary text-white'
                  : 'bg-surface-hover text-text-muted group-hover:text-text-primary'
              )}>
                <GraduationCap size={20} />
              </div>
              <div className={clsx('text-sm font-semibold', role === 'student' ? 'text-accent-primary' : 'text-text-secondary group-hover:text-text-primary')}>
                Студент
              </div>
              <div className="text-[11px] text-text-muted mt-0.5 hidden sm:block">Ищу работу</div>
            </button>
            <button
              type="button"
              onClick={() => setRole('employer')}
              className={clsx(
                'group p-4 rounded-xl border-2 text-center transition-all duration-200',
                role === 'employer'
                  ? 'border-accent-primary bg-accent-primary/10 shadow-sm shadow-accent-primary/10'
                  : 'border-border-default hover:border-border-hover hover:bg-surface-hover'
              )}
            >
              <div className={clsx(
                'w-10 h-10 rounded-xl mx-auto mb-2.5 flex items-center justify-center transition-all',
                role === 'employer'
                  ? 'bg-accent-primary text-white'
                  : 'bg-surface-hover text-text-muted group-hover:text-text-primary'
              )}>
                <Building2 size={20} />
              </div>
              <div className={clsx('text-sm font-semibold', role === 'employer' ? 'text-accent-primary' : 'text-text-secondary group-hover:text-text-primary')}>
                Работодатель
              </div>
              <div className="text-[11px] text-text-muted mt-0.5 hidden sm:block">Найти сотрудников</div>
            </button>
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
              value={form.username}
              onChange={(e) => update('username', e.target.value)}
              icon={<User size={16} />}
              required
            />

            <Input
              label="Email"
              type="email"
              placeholder="email@example.com"
              value={form.email}
              onChange={(e) => update('email', e.target.value)}
              icon={<Mail size={16} />}
              required
            />

            <div className="relative">
              <Input
                label="Пароль"
                type={showPassword ? 'text' : 'password'}
                placeholder="Минимум 6 символов"
                value={form.password}
                onChange={(e) => update('password', e.target.value)}
                icon={<Lock size={16} />}
                required
                minLength={6}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-[38px] text-text-muted hover:text-text-primary transition-colors"
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>

            <Input
              label="Подтвердите пароль"
              type="password"
              placeholder="Повторите пароль"
              value={form.confirmPassword}
              onChange={(e) => update('confirmPassword', e.target.value)}
              icon={<Lock size={16} />}
              required
              minLength={6}
            />

            <Input
              label="Телефон"
              placeholder="+992 (900) 123-45-67"
              value={form.phone}
              onChange={(e) => update('phone', e.target.value)}
              icon={<Phone size={16} />}
            />

            {role === 'employer' && (
              <Input
                label="Название компании"
                placeholder="Название вашей компании"
                value={form.companyName}
                onChange={(e) => update('companyName', e.target.value)}
                icon={<Building2 size={16} />}
              />
            )}

            <Button type="submit" loading={loading} className="w-full mt-2 h-11">
              Зарегистрироваться
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
            Уже есть аккаунт?{' '}
            <Link href="/auth/login" className="text-accent-primary hover:text-accent-primary-hover transition-colors font-semibold">
              Войти
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
