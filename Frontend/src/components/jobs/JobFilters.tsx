'use client';

import { useState, useEffect } from 'react';
import { ChevronDown, RotateCcw, Check, X } from 'lucide-react';
import { clsx } from '@/lib/utils';
import api from '@/lib/api';
import { useI18n } from '@/i18n/I18nContext';
import type { Category } from '@/types';

interface Filters {
  category: string;
  schedule: string;
  work_format: string;
  experience: string;
  no_experience: boolean;
  search: string;
}

interface JobFiltersProps {
  filters: Filters;
  onChange: (filters: Filters) => void;
}

const CATEGORY_VISIBLE_COUNT = 6;

export default function JobFilters({ filters, onChange }: JobFiltersProps) {
  const { t } = useI18n();
  const [categories, setCategories] = useState<Category[]>([]);
  const [catsExpanded, setCatsExpanded] = useState(false);

  const scheduleOptions = [
    { value: 'full_time', label: t('jobs.fullTime') },
    { value: 'part_time', label: t('jobs.partTime') },
    { value: 'flexible', label: t('jobs.flexible') },
    { value: 'shift', label: t('jobs.shift') },
  ];

  const formatOptions = [
    { value: 'remote', label: t('jobs.remote') },
    { value: 'hybrid', label: t('jobs.hybrid') },
    { value: 'office', label: t('jobs.office') },
  ];

  const experienceOptions = [
    { value: 'no_experience', label: t('jobs.noExperience') },
    { value: '1_3', label: t('experience.1_3') },
    { value: '3_5', label: t('experience.3_5') },
    { value: '5_plus', label: t('experience.5_plus') },
  ];

  useEffect(() => {
    api.get('/categories/').then((res) => {
      const data = res.data;
      setCategories(data.results || data);
    }).catch(() => {});
  }, []);

  const update = (partial: Partial<Filters>) => {
    onChange({ ...filters, ...partial });
  };

  const activeCount = [
    filters.category,
    filters.schedule,
    filters.work_format,
    filters.experience,
    filters.no_experience ? 'exp' : '',
  ].filter(Boolean).length;

  const visibleCategories = catsExpanded ? categories : categories.slice(0, CATEGORY_VISIBLE_COUNT);
  const hasMore = categories.length > CATEGORY_VISIBLE_COUNT;

  const resetAll = () => {
    onChange({ category: '', schedule: '', work_format: '', experience: '', no_experience: false, search: '' });
  };

  const SectionTitle = ({ children }: { children: React.ReactNode }) => (
    <h3 className="text-[11px] font-semibold uppercase tracking-wider text-text-subtle mb-3">
      {children}
    </h3>
  );

  const Chip = ({
    active,
    onClick,
    children,
  }: {
    active: boolean;
    onClick: () => void;
    children: React.ReactNode;
  }) => (
    <button
      onClick={onClick}
      className={clsx(
        'filter-chip-minimal group/chip',
        active && 'active'
      )}
      aria-pressed={active}
    >
      {active && <Check size={12} className="mr-1" />}
      <span>{children}</span>
      {active && (
        <X size={12} className="ml-1 opacity-50 group-hover/chip:opacity-100 transition-opacity" />
      )}
    </button>
  );

  return (
    <div className="flex flex-col gap-6">
      <div>
        <SectionTitle>{t('jobs.category')}</SectionTitle>
        <div className="flex flex-wrap gap-2">
          <Chip active={!filters.category} onClick={() => update({ category: '' })}>
            {t('jobs.all')}
          </Chip>
          {visibleCategories.map((cat) => {
            const value = String(cat.id);
            return (
              <Chip
                key={cat.id}
                active={filters.category === value}
                onClick={() => update({ category: filters.category === value ? '' : value })}
              >
                {cat.name}
              </Chip>
            );
          })}
        </div>
        {hasMore && (
          <button
            onClick={() => setCatsExpanded(!catsExpanded)}
            className="mt-2 text-[12px] text-text-muted hover:text-text-primary flex items-center gap-1 transition-colors"
          >
            <ChevronDown size={12} className={clsx('transition-transform', catsExpanded && 'rotate-180')} />
            {catsExpanded ? t('jobs.collapse') : t('jobs.moreN', { n: categories.length - CATEGORY_VISIBLE_COUNT })}
          </button>
        )}
      </div>

      <div>
        <SectionTitle>{t('jobs.schedule')}</SectionTitle>
        <div className="flex flex-wrap gap-2">
          {scheduleOptions.map((opt) => (
            <Chip
              key={opt.value}
              active={filters.schedule === opt.value}
              onClick={() => update({ schedule: filters.schedule === opt.value ? '' : opt.value })}
            >
              {opt.label}
            </Chip>
          ))}
        </div>
      </div>

      <div>
        <SectionTitle>{t('jobs.workFormat')}</SectionTitle>
        <div className="flex flex-wrap gap-2">
          {formatOptions.map((opt) => (
            <Chip
              key={opt.value}
              active={filters.work_format === opt.value}
              onClick={() => update({ work_format: filters.work_format === opt.value ? '' : opt.value })}
            >
              {opt.label}
            </Chip>
          ))}
        </div>
      </div>

      <div>
        <SectionTitle>{t('jobs.experience')}</SectionTitle>
        <div className="flex flex-wrap gap-2">
          {experienceOptions.map((opt) => (
            <Chip
              key={opt.value}
              active={filters.experience === opt.value}
              onClick={() => update({ experience: filters.experience === opt.value ? '' : opt.value })}
            >
              {opt.label}
            </Chip>
          ))}
        </div>
      </div>

      <div>
        <SectionTitle>{t('jobs.extra')}</SectionTitle>
        <label className="flex items-center gap-2.5 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.no_experience}
            onChange={(e) => update({ no_experience: e.target.checked })}
            className="w-4 h-4 rounded border-border-default bg-surface-card text-accent-primary focus:ring-2 focus:ring-accent-primary/20 accent-accent-primary"
          />
          <span className="text-[13px] text-text-secondary hover:text-text-primary transition-colors">
            {t('jobs.noExpOnly')}
          </span>
        </label>
      </div>

      {(activeCount > 0 || filters.search) && (
        <div className="pt-4 border-t border-border-default">
          <button
            onClick={resetAll}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-[13px] font-medium text-text-muted hover:text-text-primary hover:bg-surface-hover transition-colors"
          >
            <RotateCcw size={13} />
            {t('jobs.resetAll')}
          </button>
        </div>
      )}
    </div>
  );
}
