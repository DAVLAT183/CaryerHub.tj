import Link from 'next/link';
import { MapPin, Clock, Sparkles, Map, CheckCircle2 } from 'lucide-react';
import { clsx } from '@/lib/utils';
import type { Job } from '@/types';
import { formatSalary, formatSchedule, formatWorkFormat, formatDate, mediaUrl, getJobSource } from '@/lib/utils';
import { useI18n } from '@/i18n/I18nContext';

interface JobCardProps {
  job: Job;
  isFavorited?: boolean;
  isApplied?: boolean;
  onToggleFavorite?: (jobId: number) => void;
}

export default function JobCard({ job, isFavorited, isApplied, onToggleFavorite }: JobCardProps) {
  const { t } = useI18n();
  const isNew = job.created_at && new Date(job.created_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
  const sourceInfo = getJobSource(job.source);

  return (
    <Link href={`/jobs/${job.id}`} className="block group h-full">
      <article className="card-minimal h-[300px] flex flex-col">
        <div className="p-5 flex flex-col h-full min-h-0">
          <div className="flex items-start gap-4">
            {/* Logo */}
            <div className="logo-minimal">
              {job.employer?.user?.avatar ? (
                <img
                  src={mediaUrl(job.employer.user.avatar)}
                  alt={job.employer.company_name}
                  onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />
              ) : (
                <span>{job.employer?.company_name?.charAt(0) || '?'}</span>
              )}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-heading text-[15px] font-semibold text-text-primary truncate group-hover:text-accent-primary transition-colors">
                      {job.title}
                    </h3>
                    {isApplied && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded">
                        <CheckCircle2 size={10} />
                        {t('jobs.appliedBadge')}
                      </span>
                    )}
                    {isNew && <span className="new-badge">{t('jobs.new')}</span>}
                    {sourceInfo && (
                      <span className="text-[10px] font-semibold text-accent-primary bg-accent-primary/10 px-1.5 py-0.5 rounded">
                        {sourceInfo.name}
                      </span>
                    )}
                  </div>
                  <p className="text-[13px] text-text-muted mt-0.5 truncate">
                    {job.employer?.company_name || t('jobs.companyNotSpecified')}
                  </p>
                </div>

                {/* Favorite */}
                {onToggleFavorite && (
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onToggleFavorite(job.id);
                    }}
                    className="p-1.5 rounded-lg hover:bg-surface-hover transition-colors flex-shrink-0"
                    aria-label={isFavorited ? t('jobs.removeFromFavorites') : t('jobs.addToFavorites')}
                  >
                    <span className={clsx(
                      'text-lg transition-colors',
                      isFavorited ? 'text-yellow-500' : 'text-text-subtle hover:text-yellow-500'
                    )}>
                      {isFavorited ? '★' : '☆'}
                    </span>
                  </button>
                )}
              </div>

              {/* Salary */}
              <div className="mt-3 min-h-[26px]">
                {(job.salary_min || job.salary_max) && (
                  <span className="salary-badge">
                    {formatSalary(job.salary_min, job.salary_max)}
                  </span>
                )}
              </div>

              {/* Description */}
              <p className="text-[13px] text-text-secondary line-clamp-1 mt-2 min-h-[20px]">
                {job.description || ' '}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-2 mt-3">
                {job.experience_required !== undefined && (
                  <span className="tag-minimal">
                    <Sparkles size={12} />
                    {job.experience_required ? t('jobs.withExperience') : t('jobs.noExperience')}
                  </span>
                )}
                {job.work_format && (
                  <span className="tag-minimal">
                    <MapPin size={12} />
                    {formatWorkFormat(job.work_format)}
                  </span>
                )}
                {job.schedule && (
                  <span className="tag-minimal">
                    <Clock size={12} />
                    {formatSchedule(job.schedule)}
                  </span>
                )}
                {job.has_location && (
                  <span className="tag-minimal">
                    <Map size={12} className="text-accent-primary" />
                    {t('jobs.onMap')}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between mt-auto pt-3 border-t border-border-default">
            <span className="text-[11px] text-text-subtle flex items-center gap-1">
              <Clock size={11} />
              {formatDate(job.created_at)}
            </span>
            <span className="text-[12px] text-text-muted group-hover:text-accent-primary transition-colors flex items-center gap-1">
              {t('jobs.details')}
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="transition-transform group-hover:translate-x-0.5">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </span>
          </div>
        </div>
      </article>
    </Link>
  );
}
