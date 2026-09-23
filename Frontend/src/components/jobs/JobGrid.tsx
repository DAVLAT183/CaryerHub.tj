import JobCard from './JobCard';
import Skeleton from '@/components/ui/Skeleton';
import { useI18n } from '@/i18n/I18nContext';
import type { Job } from '@/types';

interface JobGridProps {
  jobs: Job[];
  loading?: boolean;
  favorites?: number[];
  appliedJobs?: number[];
  onToggleFavorite?: (jobId: number) => void;
}

export default function JobGrid({ jobs, loading, favorites = [], appliedJobs = [], onToggleFavorite }: JobGridProps) {
  const { t } = useI18n();
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 auto-rows-fr">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="glass rounded-card p-5 h-[300px]">
            <div className="flex items-start gap-3 mb-3">
              <Skeleton className="w-10 h-10 rounded-btn flex-shrink-0" />
              <div className="flex-1">
                <Skeleton className="h-4 w-3/4 mb-2" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
            <div className="flex gap-2 mb-3">
              <Skeleton className="h-5 w-20 rounded-btn" />
              <Skeleton className="h-5 w-16 rounded-btn" />
              <Skeleton className="h-5 w-14 rounded-btn" />
            </div>
            <Skeleton className="h-3 w-full mb-1" />
            <Skeleton className="h-3 w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">🔍</div>
        <h3 className="font-heading font-semibold text-lg text-soft mb-2">{t('jobs.noJobs')}</h3>
        <p className="text-sm text-muted">{t('jobs.noJobsDescriptionFull')}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 auto-rows-fr">
      {jobs.map((job) => (
        <JobCard
          key={job.id}
          job={job}
          isFavorited={favorites.includes(job.id)}
          isApplied={appliedJobs.includes(job.id)}
          onToggleFavorite={onToggleFavorite}
        />
      ))}
    </div>
  );
}
