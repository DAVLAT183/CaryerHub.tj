'use client';

import { useState, useEffect } from 'react';
import { Heart } from 'lucide-react';
import api from '@/lib/api';
import JobGrid from '@/components/jobs/JobGrid';
import Skeleton from '@/components/ui/Skeleton';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { showToast, getErrorMessage } from '@/lib/utils';
import { useI18n } from '@/i18n/I18nContext';
import type { Job } from '@/types';

export default function FavoritesPage() {
  const { t } = useI18n();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [jobIds, setJobIds] = useState<number[]>([]);
  const [appliedJobs, setAppliedJobs] = useState<number[]>([]);

  useEffect(() => {
    api.get('/favorites/').then((res) => {
      const data = res.data;
      const list = data.results || data;
      setJobs(list.map((f: { job: Job }) => f.job));
      setJobIds(list.map((f: { job: Job }) => f.job.id));
    }).catch((err) => {
      showToast(getErrorMessage(err), 'error');
    }).finally(() => setLoading(false));

    api.get('/applications/').then((res) => {
      const data = res.data;
      const list = data.results || data;
      setAppliedJobs(list.map((a: { job: number }) => a.job));
    }).catch(() => {});
  }, []);

  const removeFavorite = async (jobId: number) => {
    try {
      await api.delete(`/favorites/${jobId}/remove/`);
      setJobs((prev) => prev.filter((j) => j.id !== jobId));
      setJobIds((prev) => prev.filter((id) => id !== jobId));
      showToast(t('notifications.removedFromFavorites'), 'info');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  if (loading) {
    return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Skeleton className="h-8 w-48 mb-6" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-card" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-[1280px] mx-auto px-6 py-8">
      <Breadcrumbs items={[{ label: t('favorites.title') }]} className="mb-3" />
      <h1 className="font-heading font-bold text-2xl md:text-3xl mb-6">{t('favorites.title')}</h1>

      {jobs.length === 0 ? (
        <div className="text-center py-16">
          <Heart size={48} className="text-muted mx-auto mb-4" />
          <h3 className="font-heading font-semibold text-lg text-soft mb-2">{t('favorites.emptyJobs')}</h3>
          <p className="text-sm text-muted">{t('favorites.saveHint')}</p>
        </div>
      ) : (
        <JobGrid
          jobs={jobs}
          favorites={jobIds}
          appliedJobs={appliedJobs}
          onToggleFavorite={removeFavorite}
        />
      )}
    </div>
  );
}
