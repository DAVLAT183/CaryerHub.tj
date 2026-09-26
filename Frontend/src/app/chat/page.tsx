'use client';

import { useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Bot, Building2 } from 'lucide-react';
import AIChat from '@/components/chat/AIChat';
import EmployerChat from '@/components/chat/EmployerChat';
import { useAuth } from '@/hooks/useAuth';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { clsx } from '@/lib/utils';

type Tab = 'ai' | 'employer';

export default function ChatPage() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const userParam = searchParams.get('user');
  const [tab, setTab] = useState<Tab>(userParam ? 'employer' : 'ai');

  const tabs: { id: Tab; label: string; icon: React.ReactNode; show: boolean }[] = [
    { id: 'ai', label: 'AI Ассистент', icon: <Bot size={16} />, show: true },
    { id: 'employer', label: user?.role === 'employer' ? 'Студенты' : 'Работодатели', icon: <Building2 size={16} />, show: true },
  ];

  const visibleTabs = tabs.filter((t) => t.show);

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex items-center gap-3 sm:gap-4 px-4 sm:px-6 py-3 sm:py-4 border-b border-[var(--color-border-default)] bg-[var(--color-bg-secondary)] flex-shrink-0">
        <h1 className="font-heading font-bold text-base sm:text-lg">Чат</h1>
        <Breadcrumbs items={[{ label: 'Чат' }]} className="hidden sm:flex ml-2" />
        <div className="flex gap-0.5 sm:gap-1 p-0.5 sm:p-1 rounded-[10px] sm:rounded-[12px] bg-[var(--color-bg-primary)] border border-[var(--color-border-default)]">
          {visibleTabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={clsx(
                'flex items-center gap-1 sm:gap-1.5 px-2.5 sm:px-4 py-1.5 sm:py-2 rounded-[8px] sm:rounded-[10px] text-xs sm:text-sm font-medium transition-all',
                tab === t.id
                  ? 'bg-[var(--color-accent-primary)] text-white shadow-[0_2px_8px_rgba(16,185,129,0.3)]'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-hover)]'
              )}
            >
              {t.icon}
              <span className="hidden sm:inline">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 min-h-0">
        {tab === 'ai' && <AIChat />}
        {tab === 'employer' && <EmployerChat initialUserId={userParam ? Number(userParam) : undefined} />}
      </div>
    </div>
  );
}
