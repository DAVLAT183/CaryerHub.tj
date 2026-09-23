'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api';
import Input from '@/components/ui/Input';
import Textarea from '@/components/ui/Textarea';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { showToast, getErrorMessage } from '@/lib/utils';
import type { Category } from '@/types';

export default function CreateJobPage() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    title: '',
    description: '',
    category: '',
    salary_min: '',
    salary_max: '',
    min_age: '16',
    schedule: 'flexible',
    work_format: 'online',
    experience_required: false,
  });

  useEffect(() => {
    api.get('/categories/').then((res) => {
      const data = res.data;
      setCategories(data.results || data);
    }).catch(() => {});
  }, []);

  const update = (field: string, value: string | boolean) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        ...form,
        category: form.category ? Number(form.category) : null,
        salary_min: form.salary_min ? Number(form.salary_min) : null,
        salary_max: form.salary_max ? Number(form.salary_max) : null,
        min_age: Number(form.min_age),
      };
      const res = await api.post('/jobs/', payload);
      showToast('Вакансия опубликована!', 'success');
      router.push(`/jobs/${res.data.id}`);
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <Breadcrumbs
        items={[
          { label: 'Профиль', href: '/profile/employer' },
          { label: 'Создать вакансию' },
        ]}
        className="mb-3"
      />
      <Link href="/jobs" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-white transition-colors mb-6">
        <ArrowLeft size={14} />
        Ко всем вакансиям
      </Link>

      <h1 className="font-heading font-bold text-2xl md:text-3xl mb-6">Создать вакансию</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
        <div className="lg:col-span-2">
          <Card>
            <form onSubmit={handleSubmit} className="flex flex-col gap-5">
              <Input
                label="Название вакансии"
                placeholder="Frontend Developer"
                value={form.title}
                onChange={(e) => update('title', e.target.value)}
                required
              />

              <Select
                label="Категория"
                value={form.category}
                onChange={(value) => update('category', value)}
                options={categories.map((c) => ({ value: String(c.id), label: c.name }))}
                placeholder="Выберите категорию..."
              />

              <Textarea
                label="Описание"
                placeholder="Опишите вакансию, обязанности, условия..."
                value={form.description}
                onChange={(e) => update('description', e.target.value)}
                required
              />

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="Зарплата от (₽)"
                  type="number"
                  placeholder="30000"
                  value={form.salary_min}
                  onChange={(e) => update('salary_min', e.target.value)}
                />
                <Input
                  label="Зарплата до (₽)"
                  type="number"
                  placeholder="50000"
                  value={form.salary_max}
                  onChange={(e) => update('salary_max', e.target.value)}
                />
              </div>

              <Input
                label="Минимальный возраст"
                type="number"
                value={form.min_age}
                onChange={(e) => update('min_age', e.target.value)}
              />

              <div className="grid grid-cols-2 gap-4">
                <Select
                  label="График"
                  value={form.schedule}
                  onChange={(value) => update('schedule', value)}
                  options={[
                    { value: 'flexible', label: 'Гибкий' },
                    { value: 'part_time', label: '2-4 часа' },
                    { value: 'full_time', label: 'Полная занятость' },
                  ]}
                />
                <Select
                  label="Формат работы"
                  value={form.work_format}
                  onChange={(value) => update('work_format', value)}
                  options={[
                    { value: 'online', label: 'Онлайн' },
                    { value: 'offline', label: 'Офлайн' },
                    { value: 'hybrid', label: 'Гибрид' },
                  ]}
                />
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => update('experience_required', !form.experience_required)}
                  className={`w-10 h-5 rounded-full transition-all relative ${
                    form.experience_required ? 'bg-accent' : 'bg-white/10'
                  }`}
                >
                  <div
                    className={`w-4 h-4 rounded-full bg-white absolute top-0.5 transition-all ${
                      form.experience_required ? 'left-[22px]' : 'left-[2px]'
                    }`}
                  />
                </button>
                <span className="text-sm text-muted">Требуется опыт работы</span>
              </div>

              <Button type="submit" loading={loading}>
                Опубликовать вакансию
              </Button>
            </form>
          </Card>
        </div>

        <div>
          <Card className="sticky top-24">
            <h3 className="font-heading font-semibold mb-4">Превью</h3>
            <div className="p-3 glass rounded-card">
              <h4 className="text-sm font-semibold text-white mb-1">
                {form.title || 'Название вакансии'}
              </h4>
              <p className="text-xs text-muted mb-2">
                {form.category ? categories.find((c) => String(c.id) === form.category)?.name : 'Категория'}
              </p>
              {(form.salary_min || form.salary_max) && (
                <p className="text-xs text-accent mb-2">
                  {form.salary_min && form.salary_max
                    ? `${Number(form.salary_min).toLocaleString()} – ${Number(form.salary_max).toLocaleString()} ₽`
                    : form.salary_min
                    ? `от ${Number(form.salary_min).toLocaleString()} ₽`
                    : `до ${Number(form.salary_max).toLocaleString()} ₽`
                  }
                </p>
              )}
              <p className="text-xs text-muted line-clamp-3">
                {form.description || 'Описание вакансии...'}
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
