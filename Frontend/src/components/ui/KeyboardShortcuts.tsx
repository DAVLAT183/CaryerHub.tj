'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Keyboard, Search, Home, Bell, Heart, FileText, MessageSquare, Settings } from 'lucide-react';
import Modal from '@/components/ui/Modal';
import { clsx } from '@/lib/utils';
import { useI18n } from '@/i18n/I18nContext';

interface Shortcut {
  keys: string[];
  descriptionKey: string;
  icon: React.ReactNode;
}

const SHORTCUTS: Shortcut[] = [
  { keys: ['/'], descriptionKey: 'shortcuts.search', icon: <Search size={14} /> },
  { keys: ['g', 'h'], descriptionKey: 'shortcuts.home', icon: <Home size={14} /> },
  { keys: ['g', 'j'], descriptionKey: 'shortcuts.jobs', icon: <Search size={14} /> },
  { keys: ['g', 'f'], descriptionKey: 'shortcuts.favorites', icon: <Heart size={14} /> },
  { keys: ['g', 'a'], descriptionKey: 'shortcuts.applications', icon: <FileText size={14} /> },
  { keys: ['g', 'n'], descriptionKey: 'shortcuts.notifications', icon: <Bell size={14} /> },
  { keys: ['g', 'c'], descriptionKey: 'shortcuts.chat', icon: <MessageSquare size={14} /> },
  { keys: ['g', 's'], descriptionKey: 'shortcuts.settings', icon: <Settings size={14} /> },
  { keys: ['?'], descriptionKey: 'shortcuts.showHelp', icon: <Keyboard size={14} /> },
];

export default function KeyboardShortcuts() {
  const router = useRouter();
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [pendingG, setPendingG] = useState(false);

  const handleKey = useCallback((e: KeyboardEvent) => {
    const target = e.target as HTMLElement;
    const tag = target?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || target?.isContentEditable) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;

    if (pendingG) {
      setPendingG(false);
      const map: Record<string, string> = {
        h: '/',
        j: '/jobs',
        f: '/favorites',
        a: '/applications',
        n: '/notifications',
        c: '/chat',
        s: '/settings',
      };
      const dest = map[e.key.toLowerCase()];
      if (dest) {
        e.preventDefault();
        router.push(dest);
      }
      return;
    }

    if (e.key === 'g') {
      e.preventDefault();
      setPendingG(true);
      setTimeout(() => setPendingG(false), 1200);
      return;
    }

    if (e.key === '/') {
      e.preventDefault();
      router.push('/jobs');
      setTimeout(() => {
        const input = document.querySelector<HTMLInputElement>('input[type="search"], input[placeholder*="Поиск"], input[placeholder*="Search"]');
        input?.focus();
      }, 300);
      return;
    }

    if (e.key === '?') {
      e.preventDefault();
      setOpen((v) => !v);
    }
  }, [pendingG, router]);

  useEffect(() => {
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [handleKey]);

  return (
    <Modal open={open} onClose={() => setOpen(false)} title={t('shortcuts.title')}>
      <div className="space-y-1">
        {SHORTCUTS.map((s) => (
          <div
            key={s.descriptionKey}
            className="flex items-center justify-between py-2.5 px-2 rounded-lg hover:bg-surface-hover transition-colors"
          >
            <div className="flex items-center gap-3 text-sm text-text-primary">
              <span className="text-text-muted">{s.icon}</span>
              {t(s.descriptionKey)}
            </div>
            <div className="flex items-center gap-1">
              {s.keys.map((k, i) => (
                <span key={i}>
                  <kbd className="px-2 py-1 text-xs font-mono font-semibold bg-surface-hover border border-border-default rounded-md shadow-sm">
                    {k}
                  </kbd>
                  {i < s.keys.length - 1 && (
                    <span className="mx-1 text-xs text-text-subtle">then</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
      <p className={clsx('mt-4 text-xs text-text-muted text-center')}>
        {t('shortcuts.pressClose')} <kbd className="px-1.5 py-0.5 text-[11px] font-mono bg-surface-hover border border-border-default rounded">?</kbd> {t('shortcuts.toClose')}
      </p>
    </Modal>
  );
}
