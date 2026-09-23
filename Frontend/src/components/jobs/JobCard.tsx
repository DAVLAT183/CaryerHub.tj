import Link from 'next/link';
import { MapPin, Clock, Sparkles, Map, CheckCircle2 } from 'lucide-react';
import { clsx } from '@/lib/utils';
import type { Job } from '@/types';
import { formatSalary, formatSchedule, formatWorkFormat, formatDate, mediaUrl } from '@/lib/utils';

interface JobCardProps {
  job: Job;
  isFavorited?: boolean;
  isApplied?: boolean;
  onToggleFavorite?: (jobId: number) => void;
}

export default function JobCard({ job, isFavorited, isApplied, onToggleFavorite }: JobCardProps) {
  const isNew = job.created_at && new Date(job.created_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);

  return (
    <Link href={`/jobs/${job.id}`} className="block group">
      <article className="card-minimal">
        <div className="p-5">
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
                        Откликнут
                      </span>
                    )}
                    {isNew && <span className="new-badge">NEW</span>}
                    {job.source === 'somon_tj' && (
                      <span className="text-[10px] font-semibold text-accent-primary bg-accent-primary/10 px-1.5 py-0.5 rounded">
                        somon.tj
                      </span>
                    )}
                  </div>
                  <p className="text-[13px] text-text-muted mt-0.5 truncate">
                    {job.employer?.company_name || 'Компания не указана'}
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
                    aria-label={isFavorited ? 'Убрать из избранного' : 'Добавить в избранное'}
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
              {(job.salary_min || job.salary_max) && (
                <div className="mt-3">
                  <span className="salary-badge">
                    {formatSalary(job.salary_min, job.salary_max)}
                  </span>
                </div>
              )}

              {/* Description */}
              {job.description && (
                <p className="text-[13px] text-text-secondary line-clamp-1 mt-3">
                  {job.description}
                </p>
              )}

              {/* Tags */}
              <div className="flex flex-wrap gap-2 mt-3">
                {job.experience_required !== undefined && (
                  <span className="tag-minimal">
                    <Sparkles size={12} />
                    {job.experience_required ? 'С опытом' : 'Без опыта'}
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
                    На карте
                  </span>
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-border-default">
                <span className="text-[11px] text-text-subtle flex items-center gap-1">
                  <Clock size={11} />
                  {formatDate(job.created_at)}
                </span>
                <span className="text-[12px] text-text-muted group-hover:text-accent-primary transition-colors flex items-center gap-1">
                  Подробнее
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="transition-transform group-hover:translate-x-0.5">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </span>
              </div>
            </div>
          </div>
        </div>
      </article>
    </Link>
  );
}
