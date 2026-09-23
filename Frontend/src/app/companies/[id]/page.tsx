'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { Building2, Globe, MapPin, Briefcase, CheckCircle } from 'lucide-react';
import { clsx } from '@/lib/utils';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Card from '@/components/ui/Card';
import Skeleton from '@/components/ui/Skeleton';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import JobCard from '@/components/jobs/JobCard';
import { showToast, getErrorMessage } from '@/lib/utils';
import type { EmployerProfile, Job } from '@/types';

export default function CompanyDetailPage() {
  const params = useParams();
  const companyId = params.id as string;
  const { user } = useAuth();
  const [company, setCompany] = useState<EmployerProfile | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'about' | 'jobs'>('about');
  const [appliedJobs, setAppliedJobs] = useState<number[]>([]);

  useEffect(() => {
    Promise.all([
      api.get(`/employer-profiles/${companyId}/`).then((r) => r.data),
      api.get('/jobs/', { params: { employer: companyId } }).then((r) => (r.data.results || r.data) as Job[]),
    ]).then(([c, j]) => {
      setCompany(c);
      setJobs(j);
    }).catch((err) => {
      showToast(getErrorMessage(err), 'error');
    }).finally(() => setLoading(false));
  }, [companyId]);

  useEffect(() => {
    if (user?.role === 'student') {
      api.get('/applications/').then((res) => {
        const data = res.data;
        const list = data.results || data;
        setAppliedJobs(list.map((a: { job: number }) => a.job));
      }).catch(() => {});
    }
  }, [user]);

  if (loading) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Skeleton className="h-8 w-48 mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <Skeleton className="h-64 rounded-card" />
          <div className="lg:col-span-2">
            <Skeleton className="h-40 rounded-card mb-4" />
            <Skeleton className="h-60 rounded-card" />
          </div>
        </div>
      </div>
    );
  }

  if (!company) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Card className="p-8 sm:p-12 text-center">
          <Building2 size={48} className="text-text-muted mx-auto mb-4" />
          <h3 className="font-heading text-heading-lg text-text-primary mb-2">Компания не найдена</h3>
          <p className="font-body text-body-md text-text-muted">Возможно, компания была удалена.</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary">
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Breadcrumbs
          items={[
            { label: 'Компании', href: '/companies' },
            { label: company.company_name || 'Компания' },
          ]}
          className="mb-3"
        />
        <Card className="mb-6 sm:mb-8 animate-fade-in overflow-hidden">
          <div className="p-6 lg:p-8">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              <div className="flex items-start gap-4">
                <div className="w-16 h-16 lg:w-20 lg:h-20 rounded-xl bg-surface-hover border border-border-default flex items-center justify-center flex-shrink-0">
                  {company.user?.avatar ? (
                    <img src={company.user.avatar} alt={company.company_name} className="w-full h-full rounded-xl object-cover" />
                  ) : (
                    <span className="font-heading text-display-sm text-accent-primary">
                      {company.company_name?.charAt(0) || '?'}
                    </span>
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-3 flex-wrap">
                    <h1 className="font-heading text-heading-xl text-text-primary">
                      {company.company_name}
                    </h1>
                    {company.is_verified && (
                      <span className="flex items-center gap-1.5 px-3 py-1 bg-success/10 text-success border border-success/30 rounded-full font-body text-caption">
                        <CheckCircle size={12} />
                        Верифицирована
                      </span>
                    )}
                  </div>
                  <p className="font-body text-body-md text-text-muted mt-1">{company.user?.email}</p>
                </div>
              </div>

              {company.website && (
                <a href={company.website} target="_blank" rel="noopener noreferrer" className="btn-secondary flex items-center gap-2">
                  <Globe size={16} />
                  Сайт компании
                </a>
              )}
            </div>

            <div className="mt-6 pt-6 border-t border-border-default flex flex-wrap items-center gap-6 text-sm text-text-secondary">
              <span className="flex items-center gap-2">
                <MapPin size={14} />
                {company.address || 'Адрес не указан'}
              </span>
              <span className="flex items-center gap-2">
                <Briefcase size={14} />
                {jobs.length} вакансий
              </span>
            </div>
          </div>
        </Card>

        <div className="border-b border-border-default mb-4 sm:mb-6">
          <nav className="flex gap-8">
            <button
              onClick={() => setActiveTab('about')}
              className={clsx(
                'pb-4 font-body text-body-md font-medium border-b-2 transition-colors duration-150',
                activeTab === 'about'
                  ? 'border-accent-primary text-text-primary'
                  : 'border-transparent text-text-muted hover:text-text-primary'
              )}
            >
              О компании
            </button>
            <button
              onClick={() => setActiveTab('jobs')}
              className={clsx(
                'pb-4 font-body text-body-md font-medium border-b-2 transition-colors duration-150',
                activeTab === 'jobs'
                  ? 'border-accent-primary text-text-primary'
                  : 'border-transparent text-text-muted hover:text-text-primary'
              )}
            >
              Вакансии ({jobs.length})
            </button>
          </nav>
        </div>

        {activeTab === 'about' ? (
          <Card className="animate-fade-in">
            <div className="p-6 lg:p-8">
              <h2 className="font-heading text-heading-lg text-text-primary mb-4">О компании</h2>
              {company.description ? (
                <p className="font-body text-body-md text-text-secondary whitespace-pre-line leading-relaxed">
                  {company.description}
                </p>
              ) : (
                <p className="font-body text-body-md text-text-muted">Описание компании не добавлено.</p>
              )}
            </div>
          </Card>
        ) : (
          <div className="animate-fade-in">
            {jobs.length === 0 ? (
              <Card className="p-12 text-center">
                <Briefcase size={48} className="text-text-muted mx-auto mb-4" />
                <h3 className="font-heading text-heading-lg text-text-primary mb-2">Нет активных вакансий</h3>
                <p className="font-body text-body-md text-text-muted">У этой компании пока нет опубликованных вакансий.</p>
              </Card>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {jobs.map((job) => (
                  <JobCard key={job.id} job={job} isApplied={appliedJobs.includes(job.id)} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
