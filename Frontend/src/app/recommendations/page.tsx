'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Sparkles, MapPin, Clock, ArrowLeft, TrendingUp } from 'lucide-react';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Skeleton from '@/components/ui/Skeleton';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { formatSalary, formatSchedule, formatWorkFormat, formatDate, showToast, getErrorMessage } from '@/lib/utils';
import type { Job } from '@/types';

interface RecommendedJob extends Job {
  match_score: number;
}

export default function RecommendationsPage() {
  const { user } = useAuth();
  const [jobs, setJobs] = useState<RecommendedJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const res = await api.get<RecommendedJob[]>('/ai/recommend-jobs/');
      setJobs(res.data);
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'student') {
      fetchRecommendations();
    }
  }, [user]);

  if (user?.role !== 'student') {
    return (
      <div className="max-w-[1280px] mx-auto px-6 py-16 text-center">
        <Sparkles size={48} className="text-muted mx-auto mb-4" />
        <h2 className="font-heading font-bold text-xl mb-2">Только для студентов</h2>
        <p className="text-sm text-muted mb-4">Рекомендации ИИ доступны только студентам</p>
        <Link href="/jobs">
          <Button variant="secondary">Смотреть все вакансии</Button>
        </Link>
      </div>
    );
  }

  if (loading) {
    return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Skeleton className="h-8 w-64 mb-6" />
        <Skeleton className="h-12 w-full mb-6" />
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-card mb-3" />
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-[1280px] mx-auto px-6 py-8">
      <Breadcrumbs
        items={[
          { label: 'Профиль', href: '/profile/student' },
          { label: 'Рекомендации ИИ' },
        ]}
        className="mb-3"
      />
      <Link href="/profile/student" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-white transition-colors mb-6">
        <ArrowLeft size={14} />
        К профилю
      </Link>

      <div className="flex items-center gap-2 sm:gap-3 mb-4 sm:mb-6">
        <div className="w-10 h-10 rounded-btn bg-gradient-to-br from-accent to-accent-cyan flex items-center justify-center">
          <Sparkles size={20} className="text-white" />
        </div>
        <div>
          <h1 className="font-heading font-bold text-2xl md:text-3xl">Рекомендации ИИ</h1>
          <p className="text-sm text-muted">Вакансии, подобранные на основе вашего профиля и резюме</p>
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-16">
          <Sparkles size={48} className="text-muted mx-auto mb-4" />
          <h3 className="font-heading font-semibold text-lg text-soft mb-2">Нет рекомендаций</h3>
          <p className="text-sm text-muted mb-6">
            Заполните профиль и создайте резюме, чтобы ИИ мог подобрать вакансии
          </p>
          <Link href="/profile/student">
            <Button>Заполнить профиль</Button>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => {
            const matchPercent = Math.min(job.match_score, 100);
            const matchColor = matchPercent >= 70 ? 'text-success' : matchPercent >= 40 ? 'text-warning' : 'text-muted';

            return (
              <Link key={job.id} href={`/jobs/${job.id}`}>
                <Card hover className="relative overflow-hidden">
                  {matchPercent >= 70 && (
                    <div className="absolute top-0 right-0 w-20 h-20">
                      <div className="absolute top-2 right-2">
                        <TrendingUp size={14} className="text-success" />
                      </div>
                    </div>
                  )}

                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-btn bg-gradient-to-br from-accent/20 to-accent-cyan/20 flex items-center justify-center border border-white/[0.08]">
                        <span className="text-sm font-bold text-accent">
                          {job.employer?.company_name?.charAt(0) || '?'}
                        </span>
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-white leading-tight">{job.title}</h3>
                        <p className="text-xs text-muted mt-0.5">{job.employer?.company_name || 'Компания'}</p>
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-1">
                      <div className={`text-lg font-bold ${matchColor}`}>
                        {matchPercent}%
                      </div>
                      <span className="text-[10px] text-muted uppercase tracking-wider">совпадение</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 mb-3">
                    {(job.salary_min || job.salary_max) && (
                      <Badge variant="salary">{formatSalary(job.salary_min, job.salary_max)}</Badge>
                    )}
                    <Badge variant={job.schedule === 'flexible' ? 'flexible' : 'default'}>
                      <Clock size={10} className="mr-1" />
                      {formatSchedule(job.schedule)}
                    </Badge>
                    <Badge variant={job.work_format === 'online' ? 'online' : job.work_format === 'hybrid' ? 'hybrid' : 'offline'}>
                      <MapPin size={10} className="mr-1" />
                      {formatWorkFormat(job.work_format)}
                    </Badge>
                    {!job.experience_required && (
                      <Badge variant="no-experience">Без опыта</Badge>
                    )}
                    {job.category_name && (
                      <Badge variant="default">{job.category_name}</Badge>
                    )}
                  </div>

                  <p className="text-sm text-muted line-clamp-2 mb-3">{job.description}</p>

                  <div className="flex items-center justify-between pt-3 border-t border-white/[0.06]">
                    <span className="text-xs text-muted">
                      {formatDate(job.created_at)}
                    </span>
                    <span className="text-xs font-medium text-accent hover:text-accent-cyan transition-colors">
                      Подробнее →
                    </span>
                  </div>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
