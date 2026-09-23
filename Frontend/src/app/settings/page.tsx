'use client';

import { useState, useEffect } from 'react';
import { User, Moon, Sun, Monitor, Bell, Shield, Palette, Globe, Save, Loader2 } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/i18n/ThemeContext';
import api from '@/lib/api';
import Input from '@/components/ui/Input';
import Textarea from '@/components/ui/Textarea';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Skeleton from '@/components/ui/Skeleton';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { showToast, getErrorMessage } from '@/lib/utils';
import type { StudentProfile } from '@/types';

export default function SettingsPage() {
  const { user, updateUser } = useAuth();
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<'profile' | 'appearance' | 'notifications' | 'security'>('profile');

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    location: '',
    university: '',
    faculty: '',
    course: '',
    city: '',
    birth_date: '',
  });

  const [notifications, setNotifications] = useState({
    email_jobs: true,
    email_applications: true,
    email_messages: true,
    push_jobs: false,
    push_messages: false,
  });
  const [notifLoading, setNotifLoading] = useState(false);
  const [notifSaving, setNotifSaving] = useState(false);

  useEffect(() => {
    if (!user) return;
    setNotifLoading(true);
    api.get('/notification-settings/')
      .then((r) => {
        const d = r.data;
        setNotifications({
          email_jobs: d.email_jobs ?? true,
          email_applications: d.email_applications ?? true,
          email_messages: d.email_messages ?? true,
          push_jobs: d.push_jobs ?? false,
          push_messages: d.push_messages ?? false,
        });
      })
      .catch(() => {})
      .finally(() => setNotifLoading(false));
  }, [user]);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      api.get('/student-profiles/').then((r) => {
        const data = r.data;
        const list = data.results || data;
        return list[0] as StudentProfile;
      }),
      api.get('/users/me/').then((r) => r.data),
    ]).then(([p, u]) => {
      setProfile(p);
      if (p) {
        setForm({
          first_name: u.first_name || '',
          last_name: u.last_name || '',
          email: u.email || '',
          phone: u.phone || '',
          location: u.location || '',
          university: p.university || '',
          faculty: p.faculty || '',
          course: String(p.course || ''),
          city: p.city || '',
          birth_date: p.birth_date || '',
        });
      }
    }).catch((err) => {
      showToast(getErrorMessage(err), 'error');
    }).finally(() => setLoading(false));
  }, [user]);

  const saveProfile = async () => {
    setSaving(true);
    try {
      if (user) {
        const res = await api.patch('/users/me/', {
          first_name: form.first_name,
          last_name: form.last_name,
          phone: form.phone,
          location: form.location,
        });
        updateUser(res.data);
      }
      if (profile) {
        await api.patch(`/student-profiles/${profile.id}/`, {
          university: form.university,
          faculty: form.faculty,
          course: form.course ? parseInt(form.course) : null,
          city: form.city,
          birth_date: form.birth_date,
        });
        const res = await api.get(`/student-profiles/${profile.id}/`);
        setProfile(res.data);
      }
      showToast('Профиль сохранён', 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setSaving(false);
    }
  };

  const saveNotifications = async () => {
    setNotifSaving(true);
    try {
      await api.put('/notification-settings/', notifications);
      showToast('Настройки уведомлений сохранены', 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setNotifSaving(false);
    }
  };

  const changePassword = async () => {
    showToast('Смена пароля: перейдите в настройки аккаунта', 'info');
  };

  if (loading) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Skeleton className="h-8 w-48 mb-6" />
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 sm:gap-8">
          <Skeleton className="h-64 rounded-card" />
          <div className="lg:col-span-3 space-y-6">
            <Skeleton className="h-40 rounded-card" />
            <Skeleton className="h-40 rounded-card" />
            <Skeleton className="h-40 rounded-card" />
          </div>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'profile', label: 'Профиль', icon: User },
    { id: 'appearance', label: 'Внешний вид', icon: Palette },
    { id: 'notifications', label: 'Уведомления', icon: Bell },
    { id: 'security', label: 'Безопасность', icon: Shield },
  ];

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <Breadcrumbs items={[{ label: 'Настройки' }]} className="mb-3" />
      <h1 className="font-heading font-bold text-xl sm:text-2xl md:text-3xl mb-4 sm:mb-6">Настройки</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        <div>
          <Card className="sticky top-24">
            <div className="text-center p-6 border-b border-border-default">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-accent-primary to-accent-cyan flex items-center justify-center mx-auto mb-4">
                <User size={28} className="text-white" />
              </div>
              <h2 className="font-heading font-semibold text-lg">{user?.username}</h2>
              <p className="text-xs text-muted mt-1 capitalize">{user?.role === 'employer' ? 'Работодатель' : 'Студент'}</p>
            </div>
            <nav className="p-2 space-y-1 overflow-x-auto">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                    activeTab === tab.id
                      ? 'bg-accent-primary/10 text-accent-primary border border-accent-primary/20'
                      : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                  }`}
                >
                  <tab.icon size={16} />
                  {tab.label}
                </button>
              ))}
            </nav>
          </Card>
        </div>

        <div className="lg:col-span-3 space-y-6">
          {activeTab === 'profile' && (
            <Card>
              <div className="p-6 border-b border-border-default">
                <h3 className="font-heading font-semibold">Личные данные</h3>
                <p className="text-xs text-muted mt-1">Информация, видимая работодателям</p>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Имя"
                    value={form.first_name}
                    onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
                  />
                  <Input
                    label="Фамилия"
                    value={form.last_name}
                    onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
                  />
                </div>
                <Input
                  label="Email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  disabled
                />
                <Input
                  label="Телефон"
                  value={form.phone}
                  onChange={(e) => setForm((f) => ({ ...f, phone: e.target.value }))}
                  placeholder="+7 (xxx) xxx-xx-xx"
                />
                <Input
                  label="Место проживания"
                  value={form.location}
                  onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
                  placeholder="Душанбе, Таджикистан"
                />
                {user?.role === 'student' && (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Input
                        label="Университет"
                        value={form.university}
                        onChange={(e) => setForm((f) => ({ ...f, university: e.target.value }))}
                      />
                      <Input
                        label="Факультет"
                        value={form.faculty}
                        onChange={(e) => setForm((f) => ({ ...f, faculty: e.target.value }))}
                      />
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Input
                        label="Курс"
                        value={form.course}
                        onChange={(e) => setForm((f) => ({ ...f, course: e.target.value }))}
                        type="number"
                        min="1"
                        max="6"
                      />
                      <Input
                        label="Город"
                        value={form.city}
                        onChange={(e) => setForm((f) => ({ ...f, city: e.target.value }))}
                      />
                    </div>
                    <Input
                      label="Дата рождения"
                      type="date"
                      value={form.birth_date}
                      onChange={(e) => setForm((f) => ({ ...f, birth_date: e.target.value }))}
                    />
                  </>
                )}
                <Button onClick={saveProfile} loading={saving} className="w-full sm:w-auto">
                  <Save size={16} className="mr-2" />
                  Сохранить изменения
                </Button>
              </div>
            </Card>
          )}

          {activeTab === 'appearance' && (
            <Card>
              <div className="p-6 border-b border-border-default">
                <h3 className="font-heading font-semibold">Тема и внешний вид</h3>
                <p className="text-xs text-muted mt-1">Настройте отображение интерфейса</p>
              </div>
              <div className="p-6 space-y-6">
                <div>
                  <h4 className="font-medium text-sm text-text-secondary mb-4">Тема</h4>
                  <div className="grid grid-cols-3 gap-3">
                    {(['light', 'dark', 'system'] as const).map((t) => (
                      <button
                        key={t}
                        onClick={() => setTheme(t)}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          theme === t
                            ? 'border-accent-primary bg-accent-primary/5'
                            : 'border-border-default hover:border-border-hover'
                        }`}
                      >
                        <div className="flex items-center justify-center gap-2 mb-2">
                          {t === 'light' && <Sun size={20} className="text-warning" />}
                          {t === 'dark' && <Moon size={20} className="text-info" />}
                          {t === 'system' && <Monitor size={20} className="text-accent-primary" />}
                        </div>
                        <span className="text-sm font-medium capitalize">{t}</span>
                        <span className="text-xs text-muted block mt-1">
                          {t === 'light' && 'Светлая'}
                          {t === 'dark' && 'Тёмная'}
                          {t === 'system' && 'По системе'}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-6 border-t border-border-default">
                  <h4 className="font-medium text-sm text-text-secondary mb-4">Текущая тема: <span className="text-accent-primary capitalize">{resolvedTheme}</span></h4>
                  <div className="p-4 rounded-lg bg-surface-hover border border-border-default">
                    <p className="text-sm text-text-secondary">Предпросмотр карточки вакансии</p>
                    <div className="mt-3 p-3 rounded-card bg-surface-card border border-border-default">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-accent-primary/20 flex items-center justify-center">
                          <User size={18} className="text-accent-primary" />
                        </div>
                        <div>
                          <h5 className="font-medium text-text-primary">Frontend Developer</h5>
                          <p className="text-xs text-text-muted">TechCorp</p>
                        </div>
                      </div>
                      <div className="mt-3 flex gap-2 flex-wrap">
                        <span className="tag px-2 py-1 text-xs">100 000 - 150 000 сомони</span>
                        <span className="tag px-2 py-1 text-xs">Удалённо</span>
                        <span className="tag px-2 py-1 text-xs">Полная занятость</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {activeTab === 'notifications' && (
            <Card>
              <div className="p-6 border-b border-border-default">
                <h3 className="font-heading font-semibold">Уведомления</h3>
                <p className="text-xs text-muted mt-1">Настройте, какие уведомления получать</p>
              </div>
              <div className="p-6 space-y-6">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-8 h-8 rounded-lg bg-accent-primary/10 flex items-center justify-center">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-accent-primary"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
                    </div>
                    <div>
                      <h4 className="font-medium text-sm text-text-primary">Email уведомления</h4>
                      <p className="text-xs text-muted">Получать на почту</p>
                    </div>
                  </div>

                  <div className="rounded-xl border border-border-default divide-y divide-border-default overflow-hidden">
                    <label className="flex items-center justify-between p-4 hover:bg-surface-hover/50 transition-colors cursor-pointer group">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-blue-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-500/15 transition-colors">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-500"><path d="M16 22h2c.5 0 1-.2 1.4-.5.3-.3.5-.7.5-1.2V9.5L13.5 4H12v18h2"/><rect x="2" y="6" width="14" height="12" rx="2"/></svg>
                        </div>
                        <div>
                          <p className="font-medium text-sm text-text-primary">Новые вакансии</p>
                          <p className="text-xs text-muted">Рекомендации под ваш профиль</p>
                        </div>
                      </div>
                      <div className="relative">
                        <input
                          type="checkbox"
                          checked={notifications.email_jobs}
                          onChange={(e) => setNotifications((n) => ({ ...n, email_jobs: e.target.checked }))}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 rounded-full bg-border-default peer-checked:bg-accent-primary transition-colors duration-200" />
                        <div className="absolute left-0.5 top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200 peer-checked:translate-x-5" />
                      </div>
                    </label>

                    <label className="flex items-center justify-between p-4 hover:bg-surface-hover/50 transition-colors cursor-pointer group">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-emerald-500/15 transition-colors">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-emerald-500"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                        </div>
                        <div>
                          <p className="font-medium text-sm text-text-primary">Отклики на вакансии</p>
                          <p className="text-xs text-muted">Статус рассмотрения, приглашения на собеседование</p>
                        </div>
                      </div>
                      <div className="relative">
                        <input
                          type="checkbox"
                          checked={notifications.email_applications}
                          onChange={(e) => setNotifications((n) => ({ ...n, email_applications: e.target.checked }))}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 rounded-full bg-border-default peer-checked:bg-accent-primary transition-colors duration-200" />
                        <div className="absolute left-0.5 top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200 peer-checked:translate-x-5" />
                      </div>
                    </label>

                    <label className="flex items-center justify-between p-4 hover:bg-surface-hover/50 transition-colors cursor-pointer group">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-cyan-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-cyan-500/15 transition-colors">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-500"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22z"/></svg>
                        </div>
                        <div>
                          <p className="font-medium text-sm text-text-primary">Сообщения от работодателей</p>
                          <p className="text-xs text-muted">Новые сообщения в чате</p>
                        </div>
                      </div>
                      <div className="relative">
                        <input
                          type="checkbox"
                          checked={notifications.email_messages}
                          onChange={(e) => setNotifications((n) => ({ ...n, email_messages: e.target.checked }))}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 rounded-full bg-border-default peer-checked:bg-accent-primary transition-colors duration-200" />
                        <div className="absolute left-0.5 top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200 peer-checked:translate-x-5" />
                      </div>
                    </label>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2 mb-4">
                    <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-violet-500"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>
                    </div>
                    <div>
                      <h4 className="font-medium text-sm text-text-primary">Push уведомления</h4>
                      <p className="text-xs text-muted">Мгновенные оповещения в браузере</p>
                    </div>
                  </div>

                  <div className="rounded-xl border border-border-default divide-y divide-border-default overflow-hidden">
                    <label className="flex items-center justify-between p-4 hover:bg-surface-hover/50 transition-colors cursor-pointer group">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-amber-500/15 transition-colors">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-amber-500"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                        </div>
                        <div>
                          <p className="font-medium text-sm text-text-primary">Новые вакансии</p>
                          <p className="text-xs text-muted">Мгновенные уведомления о подходящих вакансиях</p>
                        </div>
                      </div>
                      <div className="relative">
                        <input
                          type="checkbox"
                          checked={notifications.push_jobs}
                          onChange={(e) => setNotifications((n) => ({ ...n, push_jobs: e.target.checked }))}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 rounded-full bg-border-default peer-checked:bg-accent-primary transition-colors duration-200" />
                        <div className="absolute left-0.5 top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200 peer-checked:translate-x-5" />
                      </div>
                    </label>

                    <label className="flex items-center justify-between p-4 hover:bg-surface-hover/50 transition-colors cursor-pointer group">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-rose-500/10 flex items-center justify-center flex-shrink-0 group-hover:bg-rose-500/15 transition-colors">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-rose-500"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                        </div>
                        <div>
                          <p className="font-medium text-sm text-text-primary">Сообщения</p>
                          <p className="text-xs text-muted">Уведомления о новых сообщениях в реальном времени</p>
                        </div>
                      </div>
                      <div className="relative">
                        <input
                          type="checkbox"
                          checked={notifications.push_messages}
                          onChange={(e) => setNotifications((n) => ({ ...n, push_messages: e.target.checked }))}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 rounded-full bg-border-default peer-checked:bg-accent-primary transition-colors duration-200" />
                        <div className="absolute left-0.5 top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform duration-200 peer-checked:translate-x-5" />
                      </div>
                    </label>
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <Button onClick={saveNotifications} variant="primary" loading={notifSaving} disabled={notifLoading}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mr-2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
                    Сохранить настройки
                  </Button>
                </div>
              </div>
            </Card>
          )}

          {activeTab === 'security' && (
            <Card>
              <div className="p-6 border-b border-border-default">
                <h3 className="font-heading font-semibold">Безопасность</h3>
                <p className="text-xs text-muted mt-1">Управление доступом к аккаунту</p>
              </div>
              <div className="p-6 space-y-6">
                <div className="p-4 rounded-lg bg-surface-hover border border-border-default">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Смена пароля</h4>
                      <p className="text-xs text-muted">Рекомендуется менять пароль раз в 3 месяца</p>
                    </div>
                    <Button variant="secondary" size="sm" onClick={changePassword}>
                      Изменить
                    </Button>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-surface-hover border border-border-default">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium">Двухфакторная аутентификация (2FA)</h4>
                      <p className="text-xs text-muted">Дополнительная защита аккаунта</p>
                    </div>
                    <Button variant="secondary" size="sm" disabled>
                      Настроить (скоро)
                    </Button>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-error/10 border border-error/20">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-medium text-error">Удалить аккаунт</h4>
                      <p className="text-xs text-error/80">Необратимое удаление всех данных</p>
                    </div>
                    <Button variant="secondary" size="sm" className="text-error border-error/30 hover:bg-error/10">
                      Удалить
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}