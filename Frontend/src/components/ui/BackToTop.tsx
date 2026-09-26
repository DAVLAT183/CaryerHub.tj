'use client';

import { useEffect, useState } from 'react';
import { ArrowUp } from 'lucide-react';
import { clsx } from '@/lib/utils';

export default function BackToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 400);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <button
      type="button"
      aria-label="Back to top"
      onClick={scrollToTop}
      className={clsx(
        'fixed bottom-24 right-5 z-40 w-11 h-11 rounded-full',
        'flex items-center justify-center',
        'bg-accent-primary text-white shadow-lg',
        'hover:bg-accent-primary/90 hover:-translate-y-0.5',
        'transition-all duration-200',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary focus-visible:ring-offset-2',
        visible ? 'opacity-100 translate-y-0 pointer-events-auto' : 'opacity-0 translate-y-3 pointer-events-none'
      )}
    >
      <ArrowUp size={18} />
    </button>
  );
}
