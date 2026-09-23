'use client';

import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';
import { clsx } from '@/lib/utils';
import { useI18n } from '@/i18n/I18nContext';

export interface Crumb {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: Crumb[];
  className?: string;
}

export default function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  const { t } = useI18n();
  if (!items.length) return null;

  return (
    <nav
      aria-label="Breadcrumb"
      className={clsx('flex flex-wrap items-center gap-1 text-sm text-text-muted', className)}
    >
      <Link
        href="/"
        className="flex items-center gap-1 hover:text-accent-primary transition-colors"
        aria-label="Home"
      >
        <Home size={14} />
        <span className="hidden sm:inline">{t('common.home')}</span>
      </Link>

      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        return (
          <span key={`${item.label}-${index}`} className="flex items-center gap-1">
            <ChevronRight size={14} className="text-text-subtle" />
            {item.href && !isLast ? (
              <Link
                href={item.href}
                className="hover:text-accent-primary transition-colors truncate max-w-[180px]"
              >
                {item.label}
              </Link>
            ) : (
              <span
                aria-current={isLast ? 'page' : undefined}
                className={clsx(
                  'truncate max-w-[220px]',
                  isLast && 'text-text-primary font-medium'
                )}
              >
                {item.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
