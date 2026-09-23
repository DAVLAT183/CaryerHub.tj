'use client';

import { useState, useEffect } from 'react';
import { Building2, Globe, MapPin, Pencil, CheckCircle, Download, RefreshCw, Sparkles, Plus } from 'lucide-react';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Input from '@/components/ui/Input';
import Textarea from '@/components/ui/Textarea';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Skeleton from '@/components/ui/Skeleton';
import Modal from '@/components/ui/Modal';
import Select from '@/components/ui/Select';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { formatSchedule, formatWorkFormat, showToast, getErrorMessage } from '@/lib/utils';
import type { EmployerProfile, Job, Category } from '@/types';

export default function EmployerProfilePage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<EmployerProfile | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [creating, setCreating] = useState(false);

  const [form, setForm] = useState({
    company_name: '',
    description: '',
    website: '',
    address: '',
  });

  const [locationForm, setLocationForm] = useState('');

  const [jobForm, setJobForm] = useState({
    title: '',
    description: '',
    category: '',
    salary_min: '',
    salary_max: '',
    schedule: 'flexible',
    work_format: 'online',
    experience_required: false,
    min_age: '16',
  });

  useEffect(() => {
    if (!user) return;
    Promise.all([
      api.get('/employer-profiles/').then((r) => {
        const data = r.data;
        const list = data.results || data;
        return list[0] as EmployerProfile;
      }),
      api.get('/jobs/mine/').then((r) => {
        const data = r.data;
        return (data.results || data) as Job[];
      }),
      api.get('/categories/').then((r) => {
        const data = r.data;
        return (data.results || data) as Category[];
      }),
    ]).then(([p, j, c]) => {
      setProfile(p);
      setJobs(j);
      setCategories(c);
      setLocationForm(user?.location || '');
      if (p) {
        setForm({
          company_name: p.company_name || '',
          description: p.description || '',
          website: p.website || '',
          address: p.address || '',
        });
      }
    }).catch((err) => {
      showToast(getErrorMessage(err), 'error');
    }).finally(() => setLoading(false));
  }, [user]);

  const saveProfile = async () => {
    if (!profile) return;
    try {
      await api.patch('/users/me/', { location: locationForm });
      await api.patch(`/employer-profiles/${profile.id}/`, form);
      setEditing(false);
      const res = await api.get(`/employer-profiles/${profile.id}/`);
      setProfile(res.data);
      showToast('Профиль сохранён', 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const toggleJobActive = async (jobId: number) => {
    try {
      const res = await api.post(`/jobs/${jobId}/toggle_active/`);
      setJobs((prev) =>
        prev.map((j) => (j.id === jobId ? { ...j, is_active: res.data.is_active } : j))
      );
      showToast(res.data.is_active ? 'Вакансия активирована' : 'Вакансия деактивирована', 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const handleParseSomon = async () => {
    setParsing(true);
    try {
      const res = await api.post('/parsing/somon-tj/', { max_jobs: 20 });
      if (res.data.success) {
        showToast(`Спарсено: ${res.data.created} новых, ${res.data.updated} обновлено`, 'success');
        const jobsRes = await api.get('/jobs/mine/');
        const data = jobsRes.data;
        setJobs((data.results || data) as Job[]);
      } else {
        showToast(res.data.error || 'Ошибка парсинга', 'error');
      }
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setParsing(false);
    }
  };

  const handleCreateJob = async () => {
    if (!jobForm.title.trim() || !jobForm.description.trim() || !jobForm.category) {
      showToast('Заполните обязательные поля', 'error');
      return;
    }
    setCreating(true);
    try {
      const payload: Record<string, unknown> = {
        title: jobForm.title,
        description: jobForm.description,
        category: Number(jobForm.category),
        schedule: jobForm.schedule,
        work_format: jobForm.work_format,
        experience_required: jobForm.experience_required,
        min_age: Number(jobForm.min_age) || 16,
      };
      if (jobForm.salary_min) payload.salary_min = Number(jobForm.salary_min);
      if (jobForm.salary_max) payload.salary_max = Number(jobForm.salary_max);

      await api.post('/jobs/', payload);
      setCreateOpen(false);
      setJobForm({ title: '', description: '', category: '', salary_min: '', salary_max: '', schedule: 'flexible', work_format: 'online', experience_required: false, min_age: '16' });
      showToast('Вакансия создана!', 'success');
      const res = await api.get('/jobs/mine/');
      setJobs((res.data.results || res.data) as Job[]);
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Skeleton className="h-8 w-48 mb-6" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
          <Skeleton className="h-64 rounded-card" />
          <div className="lg:col-span-2">
            <Skeleton className="h-40 rounded-card mb-4" />
            <Skeleton className="h-60 rounded-card" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <Breadcrumbs
        items={[{ label: 'Профиль', href: '/profile' }, { label: 'Работодатель' }]}
        className="mb-3"
      />
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <h1 className="font-heading font-bold text-xl sm:text-2xl md:text-3xl">Профиль работодателя</h1>
        <div className="flex gap-2 flex-wrap">
          <Button size="sm" onClick={() => setCreateOpen(true)} className="flex items-center gap-2">
            <Plus size={14} />
            Добавить вакансию
          </Button>
          <Button variant="secondary" size="sm" onClick={handleParseSomon} loading={parsing} className="flex items-center gap-2">
            <Sparkles size={14} />
            Парсинг с somon.tj
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div>
          <Card>
            <div className="text-center mb-4">
              <div className="w-16 h-16 rounded-btn bg-gradient-to-br from-accent/20 to-accent-cyan/20 flex items-center justify-center mx-auto mb-3 border border-white/[0.08]">
                <Building2 size={24} className="text-accent" />
              </div>
              <h2 className="font-heading font-semibold text-lg">{profile?.company_name || 'Компания'}</h2>
              {profile?.is_verified && (
                <span className="text-xs text-success flex items-center justify-center gap-1 mt-1">
                  <CheckCircle size={10} /> Верифицирована
                </span>
              )}
            </div>
            <p className="text-xs text-muted text-center">{user?.email}</p>
            {user?.location && (
              <div className="flex items-center justify-center gap-1 mt-2 text-xs text-muted">
                <MapPin size={12} />
                {user.location}
              </div>
            )}
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-heading font-semibold">Данные компании</h3>
              <Button variant="ghost" size="sm" onClick={() => setEditing(!editing)}>
                <Pencil size={14} className="mr-1" />
                {editing ? 'Отмена' : 'Редактировать'}
              </Button>
            </div>

            {editing ? (
              <div className="flex flex-col gap-4">
                <Input
                  label="Место проживания"
                  value={locationForm}
                  onChange={(e) => setLocationForm(e.target.value)}
                  placeholder="Душанбе, Таджикистан"
                />
                <Input
                  label="Название компании"
                  value={form.company_name}
                  onChange={(e) => setForm((f) => ({ ...f, company_name: e.target.value }))}
                />
                <Textarea
                  label="Описание"
                  value={form.description}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                />
                <Input
                  label="Сайт"
                  value={form.website}
                  onChange={(e) => setForm((f) => ({ ...f, website: e.target.value }))}
                  placeholder="https://..."
                />
                <Input
                  label="Адрес"
                  value={form.address}
                  onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
                />
                <Button onClick={saveProfile} size="sm">Сохранить</Button>
              </div>
            ) : (
              <div className="space-y-3 text-sm">
                {user?.location && (
                  <div className="flex items-center gap-2 text-muted">
                    <MapPin size={14} />
                    {user.location}
                  </div>
                )}
                <div className="flex items-center gap-2 text-muted">
                  <Building2 size={14} />
                  {profile?.company_name || '—'}
                </div>
                {profile?.description && (
                  <p className="text-soft/80 text-sm">{profile.description}</p>
                )}
                {profile?.website && (
                  <a href={profile.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-accent text-sm hover:text-accent-cyan">
                    <Globe size={14} />
                    {profile.website}
                  </a>
                )}
                {profile?.address && (
                  <div className="flex items-center gap-2 text-muted text-sm">
                    <MapPin size={14} />
                    {profile.address}
                  </div>
                )}
              </div>
            )}
          </Card>

          <Card>
            <h3 className="font-heading font-semibold mb-4">Мои вакансии ({jobs.length})</h3>
            {jobs.length === 0 ? (
              <p className="text-sm text-muted text-center py-4">У вас пока нет вакансий</p>
            ) : (
              <div className="space-y-3">
                {jobs.map((job) => (
                  <div key={job.id} className="flex items-center justify-between p-3 glass rounded-card">
                    <div>
                      <h4 className="text-sm font-medium text-soft">{job.title}</h4>
                      <div className="flex gap-2 mt-1">
                        <Badge variant={job.schedule === 'flexible' ? 'flexible' : 'default'}>
                          {formatSchedule(job.schedule)}
                        </Badge>
                        <Badge variant={job.work_format === 'online' ? 'online' : 'default'}>
                          {formatWorkFormat(job.work_format)}
                        </Badge>
                        {job.applications_count > 0 && (
                          <Badge variant="default">
                            {job.applications_count} откликов
                          </Badge>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => toggleJobActive(job.id)}
                      className={`px-3 py-1.5 rounded-btn text-xs font-medium transition-all ${
                        job.is_active
                          ? 'bg-success/12 text-success border border-success/30'
                          : 'bg-white/5 text-muted border border-white/10'
                      }`}
                    >
                      {job.is_active ? 'Активна' : 'Неактивна'}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Новая вакансия">
        <div className="flex flex-col gap-4">
          <Input
            label="Название *"
            value={jobForm.title}
            onChange={(e) => setJobForm((f) => ({ ...f, title: e.target.value }))}
            placeholder="Дизайнер, Программист, Маркетолог..."
          />
          <Select
            label="Категория *"
            value={jobForm.category}
            onChange={(e) => setJobForm((f) => ({ ...f, category: e.target.value }))}
            options={[{ value: '', label: 'Выберите категорию' }, ...categories.map((c) => ({ value: String(c.id), label: c.name }))]}
          />
          <Textarea
            label="Описание *"
            value={jobForm.description}
            onChange={(e) => setJobForm((f) => ({ ...f, description: e.target.value }))}
            placeholder="Опишите обязанности, требования, условия..."
            rows={4}
          />
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Мин. зарплата"
              type="number"
              value={jobForm.salary_min}
              onChange={(e) => setJobForm((f) => ({ ...f, salary_min: e.target.value }))}
              placeholder="0"
            />
            <Input
              label="Макс. зарплата"
              type="number"
              value={jobForm.salary_max}
              onChange={(e) => setJobForm((f) => ({ ...f, salary_max: e.target.value }))}
              placeholder="0"
            />
          </div>
          <Select
            label="График"
            value={jobForm.schedule}
            onChange={(e) => setJobForm((f) => ({ ...f, schedule: e.target.value }))}
            options={[
              { value: 'flexible', label: 'Гибкий' },
              { value: 'part_time', label: '2-4 часа' },
              { value: 'full_time', label: 'Полная занятость' },
            ]}
          />
          <Select
            label="Формат работы"
            value={jobForm.work_format}
            onChange={(e) => setJobForm((f) => ({ ...f, work_format: e.target.value }))}
            options={[
              { value: 'online', label: 'Онлайн' },
              { value: 'offline', label: 'Офлайн' },
              { value: 'hybrid', label: 'Гибрид' },
            ]}
          />
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="exp_required"
              checked={jobForm.experience_required}
              onChange={(e) => setJobForm((f) => ({ ...f, experience_required: e.target.checked }))}
              className="rounded"
            />
            <label htmlFor="exp_required" className="text-sm text-soft">Требуется опыт</label>
          </div>
          <Input
            label="Мин. возраст"
            type="number"
            value={jobForm.min_age}
            onChange={(e) => setJobForm((f) => ({ ...f, min_age: e.target.value }))}
            min={16}
          />
          <Button onClick={handleCreateJob} loading={creating}>
            Создать вакансию
          </Button>
        </div>
      </Modal>
    </div>
  );
}
