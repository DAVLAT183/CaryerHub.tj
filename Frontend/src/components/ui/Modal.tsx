'use client';

import { useEffect, type ReactNode } from 'react';
import { X } from 'lucide-react';
import { clsx } from '@/lib/utils';

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  className?: string;
}

export default function Modal({ open, onClose, title, children, className }: ModalProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (open) window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center">
      <div
        className="absolute inset-0"
        style={{ backgroundColor: 'rgba(20, 24, 30, 0.30)' }}
        onClick={onClose}
      />
      <div
        className={clsx(
          'relative z-10 bg-surface-card rounded-2xl p-8 border border-border-default shadow-[0_10px_35px_rgba(20,30,40,0.10)]',
          'w-full max-w-lg mx-4 animate-fade-in max-h-[90vh] overflow-y-auto',
          className
        )}
      >
        <div className="flex items-center justify-between mb-6">
          {title && <h2 className="text-xl font-heading font-semibold">{title}</h2>}
          <button
            onClick={onClose}
            className="ml-auto p-2 text-text-muted hover:text-text-primary rounded-full hover:bg-surface-hover transition-colors"
          >
            <X size={20} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
