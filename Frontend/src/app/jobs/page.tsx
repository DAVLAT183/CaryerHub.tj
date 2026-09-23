'use client';

import { useState, useEffect, useCallback } from 'react';
import { Search, Filter, X } from 'lucide-react';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import JobFilters from '@/components/jobs/JobFilters';
import JobCard from '@/components/jobs/JobCard';
import Card from '@/components/ui/Card';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { showToast, getErrorMessage, formatVacancyWord } from '@/lib/utils';
import { useI18n } from '@/i18n/I18nContext';
import type { Job, PaginatedResponse } from '@/types';

interface Filters {
  category: string;
  schedule: string;
  work_format: string;
  experience: string;
  no_experience: boolean;
  search: string;
  page: number;
}

const initialFilters: Filters = {
  category: '',
  schedule: '',
  work_format: '',
  experience: '',
  no_experience: false,
  search: '',
  page: 1,
};

export default function JobsPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [favorites, setFavorites] = useState<number[]>([]);
  const [appliedJobs, setAppliedJobs] = useState<number[]>([]);
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [showMobileFilters, setShowMobileFilters] = useState(false);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string | number> = { page: filters.page };
      if (filters.category) params.category = filters.category;
      if (filters.schedule) params.schedule = filters.schedule;
      if (filters.work_format) params.work_format = filters.work_format;
      if (filters.experience) params.experience_level = filters.experience;
      if (filters.no_experience) params.no_experience = 'true';
      if (filters.search) params.search = filters.search;

      const res = await api.get<PaginatedResponse<Job>>('/jobs/', { params });
      setJobs(res.data.results);
      setCount(res.data.count);
    } catch {
      setJobs([]);
      setCount(0);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  useEffect(() => {
    api.get('/favorites/').then((res) => {
      const data = res.data;
      const list = data.results || data;
      setFavorites(list.map((f: { job_id: number }) => f.job_id));
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (user?.role === 'student') {
      api.get('/applications/').then((res) => {
        const data = res.data;
        const list = data.results || data;
        setAppliedJobs(list.map((a: { job: number }) => a.job));
      }).catch(() => {});
    }
  }, [user]);

  const toggleFavorite = async (jobId: number) => {
    try {
      if (favorites.includes(jobId)) {
        await api.delete(`/favorites/${jobId}/remove/`);
        setFavorites((prev) => prev.filter((id) => id !== jobId));
        showToast(t('notifications.removedFromFavorites'), 'info');
      } else {
        await api.post('/favorites/add/', { job_id: jobId });
        setFavorites((prev) => [...prev, jobId]);
        showToast(t('notifications.addedToFavorites'), 'success');
      }
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const handleFilterChange = (newFilters: Partial<Filters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handleSearchChange = (value: string) => {
    setFilters((prev) => ({ ...prev, search: value, page: 1 }));
  };

  const hasActiveFilters = filters.category || filters.schedule || filters.work_format || filters.experience || filters.no_experience;

  const totalPages = Math.ceil(count / 10);

  const paginationNumbers = Array.from({ length: totalPages }, (_, i) => i + 1).slice(
    Math.max(0, page - 2),
    Math.min(totalPages, page + 2)
  );

  return (
    <div className="min-h-screen bg-bg-primary">
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Breadcrumbs items={[{ label: t('nav.jobs') }]} className="mb-3" />
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h1 className="font-heading text-[28px] font-bold text-text-primary tracking-tight">
                {t('nav.jobs')}
              </h1>
              <p className="text-[14px] text-text-muted mt-1">
                {t('jobs.foundCount', { count, word: formatVacancyWord(count) })}
              </p>
            </div>
            <button
              onClick={() => setShowMobileFilters(true)}
              className="lg:hidden flex items-center gap-2 px-4 py-2.5 rounded-xl border border-border-default bg-surface-card text-text-secondary hover:bg-surface-hover transition-colors text-[13px] font-medium"
            >
              <Filter size={16} />
              {t('jobs.filters')}
              {hasActiveFilters && (
                <span className="w-5 h-5 text-[10px] font-semibold bg-accent-primary text-white rounded-full flex items-center justify-center">
                  {Object.values(filters).filter(v => v).length - 1}
                </span>
              )}
            </button>
          </div>
        </div>

        <div className="flex gap-8">
          {/* Sidebar Filters */}
          <aside className="hidden lg:block w-[280px] flex-shrink-0">
            <div className="filter-minimal sticky top-8">
              <JobFilters filters={filters} onChange={handleFilterChange} />
            </div>
          </aside>

          {/* Main Content */}
          <div className="flex-1 min-w-0">
            {/* Search Bar */}
            <div className="mb-6">
              <div className="search-minimal">
                <Search className="search-icon w-5 h-5" aria-hidden="true" />
                <input
                  type="text"
                  value={filters.search}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  placeholder={t('jobs.searchPlaceholderFull')}
                  aria-label={t('jobs.searchLabel')}
                />
                {filters.search && (
                  <button
                    onClick={() => handleSearchChange('')}
                    className="absolute right-4 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-text-subtle hover:text-text-primary hover:bg-surface-hover transition-colors"
                    aria-label={t('jobs.clearSearch')}
                  >
                    <X size={16} />
                  </button>
                )}
              </div>
            </div>

            {/* Loading State */}
            {loading ? (
              <div className="grid gap-4 grid-cols-1 lg:grid-cols-2 auto-rows-fr" role="status" aria-label={t('jobs.loading')}>
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="card-minimal h-[300px] p-5 animate-pulse">
                    <div className="flex gap-4">
                      <div className="w-11 h-11 rounded-xl bg-surface-hover flex-shrink-0" />
                      <div className="flex-1 space-y-3">
                        <div className="h-4 bg-surface-hover rounded w-3/4" />
                        <div className="h-3 bg-surface-hover rounded w-1/2" />
                        <div className="h-5 bg-surface-hover rounded w-24 mt-2" />
                        <div className="flex gap-2 mt-3">
                          <div className="h-6 bg-surface-hover rounded-lg w-16" />
                          <div className="h-6 bg-surface-hover rounded-lg w-20" />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : jobs.length === 0 ? (
              <div className="card-minimal p-12 text-center">
                <div className="w-16 h-16 rounded-2xl bg-surface-hover flex items-center justify-center mx-auto mb-4">
                  <Search size={28} className="text-text-subtle" />
                </div>
                <h3 className="font-heading text-[17px] font-semibold text-text-primary mb-2">
                  {t('jobs.noJobs')}
                </h3>
                <p className="text-[13px] text-text-muted mb-6 max-w-sm mx-auto">
                  {t('jobs.noJobsDescriptionFull')}
                </p>
                <button
                  onClick={() => setFilters(initialFilters)}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-[13px] font-medium text-text-muted hover:text-text-primary hover:bg-surface-hover transition-colors"
                >
                  <X size={14} />
                  {t('jobs.resetFilters')}
                </button>
              </div>
            ) : (
              <>
                {/* Job Grid - 2 columns */}
                <div className="grid gap-4 grid-cols-1 lg:grid-cols-2 auto-rows-fr" role="list" aria-label={t('jobs.listLabel')}>
                  {jobs.map((job) => (
                    <JobCard
                      key={job.id}
                      job={job}
                      isFavorited={favorites.includes(job.id)}
                      isApplied={appliedJobs.includes(job.id)}
                      onToggleFavorite={toggleFavorite}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <nav className="flex items-center justify-center gap-2 mt-10" aria-label={t('jobs.pagination')}>
                    <button
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="w-10 h-10 rounded-xl border border-border-default bg-surface-card text-text-muted hover:bg-surface-hover disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
                      aria-label={t('jobs.prevPage')}
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M15 18l-6-6 6-6" />
                      </svg>
                    </button>
                    {page > 3 && (
                      <>
                        <button
                          onClick={() => setPage(1)}
                          className={`w-10 h-10 rounded-xl flex items-center justify-center text-[13px] font-medium transition-colors ${page === 1 ? 'bg-accent-primary text-white' : 'border border-border-default bg-surface-card text-text-muted hover:bg-surface-hover'}`}
                          aria-label={t('jobs.pageN', { n: 1 })}
                        >
                          1
                        </button>
                        {page > 4 && <span className="w-10 h-10 flex items-center justify-center text-text-muted text-[13px]">...</span>}
                      </>
                    )}
                    {paginationNumbers.map((p) => (
                      <button
                        key={p}
                        onClick={() => setPage(p)}
                        className={`w-10 h-10 rounded-xl flex items-center justify-center text-[13px] font-medium transition-colors ${page === p ? 'bg-accent-primary text-white' : 'border border-border-default bg-surface-card text-text-muted hover:bg-surface-hover'}`}
                        aria-label={t('jobs.pageN', { n: p })}
                        aria-current={page === p ? 'page' : undefined}
                      >
                        {p}
                      </button>
                    ))}
                    {page < totalPages - 2 && (
                      <>
                        {page < totalPages - 3 && <span className="w-10 h-10 flex items-center justify-center text-text-muted text-[13px]">...</span>}
                        <button
                          onClick={() => setPage(totalPages)}
                          className={`w-10 h-10 rounded-xl flex items-center justify-center text-[13px] font-medium transition-colors ${page === totalPages ? 'bg-accent-primary text-white' : 'border border-border-default bg-surface-card text-text-muted hover:bg-surface-hover'}`}
                          aria-label={t('jobs.pageN', { n: totalPages })}
                        >
                          {totalPages}
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                      className="w-10 h-10 rounded-xl border border-border-default bg-surface-card text-text-muted hover:bg-surface-hover disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
                      aria-label={t('jobs.nextPage')}
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M9 18l6-6-6-6" />
                      </svg>
                    </button>
                  </nav>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Filters Drawer */}
      {showMobileFilters && (
        <div className="fixed inset-0 z-[300] lg:hidden">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowMobileFilters(false)} />
          <div className="absolute right-0 top-0 bottom-0 w-full max-w-sm bg-bg-primary border-l border-border-default p-6 overflow-y-auto animate-slide-up">
            <div className="flex items-center justify-between mb-6 sticky top-0 bg-bg-primary/90 backdrop-blur-sm pb-4 border-b border-border-default z-10">
              <div className="flex items-center gap-2.5">
                <Filter size={16} className="text-accent-primary" />
                <h2 className="font-heading text-[17px] font-semibold text-text-primary">{t('jobs.filters')}</h2>
                {hasActiveFilters && (
                  <span className="px-2 py-0.5 text-[10px] font-semibold text-accent-primary bg-accent-primary/10 rounded-lg">
                    {Object.values(filters).filter(v => v).length - 1}
                  </span>
                )}
              </div>
              <button
                onClick={() => setShowMobileFilters(false)}
                className="p-2 rounded-xl hover:bg-surface-hover transition-colors text-text-muted"
              >
                <X size={18} />
              </button>
            </div>
            <JobFilters filters={filters} onChange={handleFilterChange} />
          </div>
        </div>
      )}
    </div>
  );
}
