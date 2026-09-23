'use client';

import { useState, useEffect } from 'react';
import { FileText, Clock } from 'lucide-react';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Badge from '@/components/ui/Badge';
import Card from '@/components/ui/Card';
import Select from '@/components/ui/Select';
import Skeleton from '@/components/ui/Skeleton';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { formatDate, formatStatus, clsx, showToast, getErrorMessage } from '@/lib/utils';
import { useI18n } from '@/i18n/I18nContext';
import type { Application } from '@/types';

export default function ApplicationsPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    api.get('/applications/').then((res) => {
      const data = res.data;
      setApplications(data.results || data);
    }).catch((err) => {
      showToast(getErrorMessage(err), 'error');
    }).finally(() => setLoading(false));
  }, [user]);

  const updateStatus = async (id: number, newStatus: string) => {
    try {
      await api.post(`/applications/${id}/update_status/`, { status: newStatus });
      setApplications((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: newStatus as Application['status'] } : a))
      );
      showToast(t('applications.statusUpdated'), 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  if (loading) {
    return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Skeleton className="h-8 w-48 mb-6" />
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-card mb-3" />
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-[1280px] mx-auto px-6 py-8">
      <Breadcrumbs
        items={[
          { label: user?.role === 'student' ? t('applications.title') : t('employer.applications') },
        ]}
        className="mb-3"
      />
      <h1 className="font-heading font-bold text-2xl md:text-3xl mb-6">
        {user?.role === 'student' ? t('applications.title') : t('employer.applications')}
      </h1>

      {applications.length === 0 ? (
        <div className="text-center py-16">
          <FileText size={48} className="text-muted mx-auto mb-4" />
          <h3 className="font-heading font-semibold text-lg text-soft mb-2">{t('applications.empty')}</h3>
          <p className="text-sm text-muted">
            {user?.role === 'student'
              ? t('applications.emptyStudent')
              : t('applications.emptyEmployer')
            }
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {applications.map((app) => (
            <Card key={app.id}>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-soft truncate">{app.job_title}</h3>
                  <p className="text-xs text-muted mt-0.5">
                    {user?.role === 'student'
                      ? app.job_employer_name || t('nav.employer')
                      : t('applications.from', { name: app.student_name })
                    }
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant={`status-${app.status}` as any}>
                      {formatStatus(app.status)}
                    </Badge>
                    <span className="text-xs text-muted flex items-center gap-1">
                      <Clock size={10} />
                      {formatDate(app.created_at)}
                    </span>
                  </div>
                  {app.cover_letter && (
                    <p className="text-xs text-muted mt-2 line-clamp-2">{app.cover_letter}</p>
                  )}
                </div>

                {user?.role === 'employer' && (
                  <div className="sm:ml-4 flex-shrink-0 w-full sm:w-44">
                    <Select
                      value={app.status}
                      onChange={(value) => updateStatus(app.id, value)}
                      options={[
                        { value: 'sent', label: t('applications.status.sent') },
                        { value: 'viewed', label: t('applications.status.viewed') },
                        { value: 'interview', label: t('applications.status.interview') },
                        { value: 'accepted', label: t('applications.status.accepted') },
                        { value: 'rejected', label: t('applications.status.rejected') },
                      ]}
                    />
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
