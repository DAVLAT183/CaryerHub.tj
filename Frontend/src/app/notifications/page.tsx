'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Bell, Check, CheckCheck, Info, Eye, XCircle, CheckCircle, Calendar, MessageSquare } from 'lucide-react';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Avatar from '@/components/ui/Avatar';
import Skeleton from '@/components/ui/Skeleton';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { formatDate, clsx, showToast, getErrorMessage } from '@/lib/utils';
import type { Notification } from '@/types';

const typeIcons: Record<string, typeof Bell> = {
  application_viewed: Eye,
  application_accepted: CheckCircle,
  application_rejected: XCircle,
  application_interview: Calendar,
  message: MessageSquare,
  system: Info,
};

const typeColors: Record<string, string> = {
  application_viewed: 'text-blue-400',
  application_accepted: 'text-emerald-400',
  application_rejected: 'text-red-400',
  application_interview: 'text-amber-400',
  message: 'text-cyan-400',
  system: 'text-text-muted',
};

export default function NotificationsPage() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    api.get('/notifications/').then((res) => {
      const data = res.data;
      setNotifications(data.results || data);
    }).catch((err) => {
      showToast(getErrorMessage(err), 'error');
    }).finally(() => setLoading(false));
  }, [user]);

  const markAsRead = async (id: number) => {
    try {
      await api.post(`/notifications/${id}/mark_read/`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const markAllAsRead = async () => {
    try {
      await api.post('/notifications/mark_all_read/');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      showToast('Все уведомления отмечены как прочитанные', 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  if (loading) {
    return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Skeleton className="h-8 w-48 mb-6" />
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-20 rounded-card mb-3" />
        ))}
      </div>
    );
  }

  return (
    <div className="max-w-[1280px] mx-auto px-6 py-8">
      <Breadcrumbs items={[{ label: 'Уведомления' }]} className="mb-3" />
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 sm:mb-6">
        <h1 className="font-heading font-bold text-2xl md:text-3xl">
          Уведомления
        </h1>
        {unreadCount > 0 && (
          <button
            onClick={markAllAsRead}
            className="btn-ghost text-sm flex items-center gap-2"
          >
            <CheckCheck size={16} />
            Отметить все прочитанными
          </button>
        )}
      </div>

      {notifications.length === 0 ? (
        <div className="text-center py-16">
          <Bell size={48} className="text-muted mx-auto mb-4" />
          <h3 className="font-heading font-semibold text-lg text-soft mb-2">Нет уведомлений</h3>
          <p className="text-sm text-muted">
            Здесь будут появляться уведомления о статусе ваших откликов
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {notifications.map((notification) => {
            const Icon = typeIcons[notification.notification_type] || Bell;
            const iconColor = typeColors[notification.notification_type] || 'text-text-muted';

            return (
              <div
                key={notification.id}
                className={clsx(
                  'rounded-card border transition-all duration-150',
                  notification.is_read
                    ? 'bg-surface-card border-border-default'
                    : 'bg-accent-primary/[0.04] border-accent-primary/20'
                )}
              >
                <div className="flex items-start gap-4 p-4">
                  {notification.employer_avatar ? (
                    <Avatar src={notification.employer_avatar} alt="" size="md" />
                  ) : (
                    <div className={clsx(
                      'w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0',
                      notification.is_read ? 'bg-surface-hover' : 'bg-accent-primary/10'
                    )}>
                      <Icon size={18} className={iconColor} />
                    </div>
                  )}

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text-primary leading-snug">
                          {notification.message}
                        </p>
                        <div className="flex items-center gap-3 mt-1.5">
                          <span className="text-xs text-text-muted flex items-center gap-1">
                            <Bell size={10} />
                            {formatDate(notification.created_at)}
                          </span>
                          {!notification.is_read && (
                            <span className="w-2 h-2 rounded-full bg-accent-primary flex-shrink-0" />
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-1 flex-shrink-0">
                        {notification.link && (
                          <Link
                            href={notification.link}
                            onClick={() => !notification.is_read && markAsRead(notification.id)}
                            className="btn-ghost text-xs px-2 py-1"
                          >
                            Перейти
                          </Link>
                        )}
                        {!notification.is_read && (
                          <button
                            onClick={() => markAsRead(notification.id)}
                            className="btn-icon p-1.5"
                            title="Отметить как прочитанное"
                          >
                            <Check size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
