'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Search, Building2, MapPin, Globe, X } from 'lucide-react';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Skeleton from '@/components/ui/Skeleton';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { showToast, getErrorMessage } from '@/lib/utils';
import type { EmployerProfile } from '@/types';

interface CompanyFilters {
  search: string;
  page: number;
}

const initialFilters: CompanyFilters = {
  search: '',
  page: 1,
};

export default function CompaniesPage() {
  const [companies, setCompanies] = useState<EmployerProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [count, setCount] = useState(0);
  const [filters, setFilters] = useState<CompanyFilters>(initialFilters);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string | number> = { page: filters.page };
    if (filters.search) params.search = filters.search;

    api.get<{ count: number; results: EmployerProfile[] }>('/employer-profiles/', { params })
      .then((res) => {
        setCompanies(res.data.results);
        setCount(res.data.count);
      })
      .catch((err) => {
        setCompanies([]);
        setCount(0);
        showToast(getErrorMessage(err), 'error');
      })
      .finally(() => setLoading(false));
  }, [filters]);

  const totalPages = Math.ceil(count / 10);

  return (
    <div className="min-h-screen bg-bg-primary">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Breadcrumbs items={[{ label: 'Компании' }]} className="mb-3" />
        <div className="mb-8 animate-fade-in">
          <h1 className="font-heading text-display-md text-text-primary tracking-tight font-semibold">
            Компании
          </h1>
          <p className="font-body text-body-md text-text-muted mt-1">
            {count} компаний найдено
          </p>
        </div>

        <div className="card p-4 mb-6 animate-fade-in">
          <div className="relative max-w-md">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-subtle" />
            <input
              type="text"
              value={filters.search}
              onChange={(e) => setFilters({ search: e.target.value, page: 1 })}
              placeholder="Поиск по названию, описанию..."
              className="input pl-12 w-full"
              aria-label="Поиск компаний"
            />
          </div>
        </div>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Card key={i} className="p-5 animate-pulse space-y-3">
                <div className="h-4 bg-surface-hover rounded w-3/4" />
                <div className="h-4 bg-surface-hover rounded w-1/2" />
                <div className="h-4 bg-surface-hover rounded w-2/3" />
              </Card>
            ))}
          </div>
        ) : companies.length === 0 ? (
          <Card className="p-12 text-center animate-fade-in">
            <Building2 size={48} className="text-text-subtle mx-auto mb-4" />
            <h3 className="font-heading text-heading-lg text-text-primary mb-2">
              Компании не найдены
            </h3>
            <p className="font-body text-body-md text-text-muted mb-6 max-w-md mx-auto">
              Попробуйте изменить поисковый запрос.
            </p>
            <button onClick={() => setFilters(initialFilters)} className="btn-ghost">
              Сбросить поиск
            </button>
          </Card>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {companies.map((company) => (
                <Link key={company.id} href={`/companies/${company.id}`} className="block">
                  <Card className="p-5 group hover:border-border-hover hover:bg-surface-hover transition-all duration-150">
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-12 h-12 rounded-lg bg-surface-hover border border-border-default flex items-center justify-center flex-shrink-0">
                        {company.user?.avatar ? (
                          <img src={company.user.avatar} alt={company.company_name} className="w-full h-full rounded-lg object-cover" />
                        ) : (
                          <span className="font-heading text-heading-md text-accent-primary">
                            {company.company_name?.charAt(0) || '?'}
                          </span>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="font-heading text-heading-md text-text-primary truncate group-hover:text-accent-primary transition-colors duration-150">
                          {company.company_name}
                        </h3>
                        <p className="font-body text-body-sm text-text-muted mt-0.5 truncate">
                          {company.user?.email || 'Email не указан'}
                        </p>
                      </div>
                    </div>

                    {company.description && (
                      <p className="font-body text-body-sm text-text-secondary line-clamp-2 mb-3">
                        {company.description}
                      </p>
                    )}

                    <div className="flex flex-wrap gap-2 mb-3">
                      {company.address && (
                        <span className="tag flex items-center gap-1.5">
                          <MapPin size={12} className="text-text-muted" />
                          {company.address}
                        </span>
                      )}
                      {company.website && (
                        <span className="tag flex items-center gap-1.5 text-accent-primary">
                          <Globe size={12} />
                          Сайт
                        </span>
                      )}
                      {company.is_verified && (
                        <Badge variant="default">Верифицирована</Badge>
                      )}
                    </div>

                    <div className="pt-3 border-t border-border-default">
                      <span className="font-body text-body-sm text-text-muted group-hover:text-accent-primary transition-colors duration-150 flex items-center gap-1">
                        Профиль компании
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="inline-block transition-transform duration-150 group-hover:translate-x-1">
                          <path d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                      </span>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>

            {totalPages > 1 && (
              <nav className="flex items-center justify-center gap-2 mt-10" aria-label="Пагинация">
                <button
                  onClick={() => setFilters((p) => ({ ...p, page: Math.max(1, p.page - 1) }))}
                  disabled={filters.page === 1}
                  className="btn-secondary p-0 w-10 h-10 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M15 18l-6-6 6-6" />
                  </svg>
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).slice(
                  Math.max(0, filters.page - 3), Math.min(totalPages, filters.page + 2)
                ).map((p) => (
                  <button
                    key={p}
                    onClick={() => setFilters((prev) => ({ ...prev, page: p }))}
                    className={filters.page === p ? 'btn-primary w-10 h-10' : 'btn-secondary w-10 h-10'}
                  >
                    {p}
                  </button>
                ))}
                <button
                  onClick={() => setFilters((p) => ({ ...p, page: Math.min(totalPages, p.page + 1) }))}
                  disabled={filters.page === totalPages}
                  className="btn-secondary p-0 w-10 h-10 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </button>
              </nav>
            )}
          </>
        )}
      </div>
    </div>
  );
}
