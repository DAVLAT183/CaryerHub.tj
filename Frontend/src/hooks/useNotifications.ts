'use client';

import { useEffect, useCallback, useState, useRef } from 'react';
import api from '@/lib/api';
import { useWebSocket } from './useWebSocket';

interface Notification {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

interface UseNotificationsReturn {
  notifications: Notification[];
  unreadCount: number;
  loading: boolean;
  markAsRead: (id: number) => Promise<void>;
  markAllAsRead: () => Promise<void>;
  refresh: () => Promise<void>;
}

export function useNotifications(enabled = true): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const fetchRef = useRef(false);

  const fetchNotifications = useCallback(async () => {
    if (fetchRef.current) return;
    fetchRef.current = true;
    try {
      const [listRes, countRes] = await Promise.all([
        api.get('/notifications/'),
        api.get('/notifications/unread_count/'),
      ]);
      const data = listRes.data;
      setNotifications(data.results || data);
      setUnreadCount(countRes.data.unread_count);
    } catch {
      // silent
    } finally {
      setLoading(false);
      fetchRef.current = false;
    }
  }, []);

  useEffect(() => {
    if (enabled) fetchNotifications();
  }, [enabled, fetchNotifications]);

  const handleWsMessage = useCallback((msg: Record<string, unknown>) => {
    if (msg.type === 'application_new') return;

    let payload: Record<string, unknown> = msg;
    if (msg.type === 'notification' && msg.data && typeof msg.data === 'object') {
      payload = msg.data as Record<string, unknown>;
    }

    if (msg.type === 'send_notification' || msg.type === 'notification' || payload.notification_type) {
      const newNotif: Notification = {
        id: typeof payload.id === 'number' ? payload.id : Date.now(),
        notification_type: (payload.notification_type as string) || 'info',
        title: (payload.title as string) || '',
        message: (payload.message as string) || '',
        link: (payload.link as string) || null,
        is_read: false,
        created_at: (payload.created_at as string) || new Date().toISOString(),
      };
      setNotifications((prev) => {
        if (prev.some((n) => n.id === newNotif.id)) return prev;
        return [newNotif, ...prev];
      });
      setUnreadCount((prev) => prev + 1);
    }
  }, []);

  const { isConnected } = useWebSocket({
    path: '/ws/notifications/',
    onMessage: handleWsMessage,
    enabled,
  });

  const markAsRead = useCallback(async (id: number) => {
    try {
      await api.patch(`/notifications/${id}/`, { is_read: true });
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch {
      // silent
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      await api.post('/notifications/mark_all_read/');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      // silent
    }
  }, []);

  return {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    markAllAsRead,
    refresh: fetchNotifications,
  };
}
