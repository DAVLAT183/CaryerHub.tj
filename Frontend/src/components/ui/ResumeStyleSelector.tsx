'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { clsx } from '@/lib/utils';
import { useI18n } from '@/i18n/I18nContext';
import type { ResumeStyle } from '@/types';

interface StyleOption {
  value: ResumeStyle;
  label: string;
  color: string;
  description: string;
}

const STYLE_META: Record<string, { color: string; descKey: string }> = {
  classic: { color: '#10B981', descKey: 'resumeStyles.classicDesc' },
  minimal: { color: '#6B7078', descKey: 'resumeStyles.minimalDesc' },
  creative: { color: '#F59E0B', descKey: 'resumeStyles.creativeDesc' },
};

const STYLE_OPTIONS: StyleOption[] = (['classic', 'minimal', 'creative'] as ResumeStyle[]).map((v) => ({
  value: v,
  label: v,
  color: STYLE_META[v].color,
  description: STYLE_META[v].descKey,
}));

interface ResumeStyleSelectorProps {
  value: ResumeStyle | string;
  onChange?: (style: ResumeStyle) => void;
  label?: string;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  compact?: boolean;
}

export default function ResumeStyleSelector({
  value,
  onChange,
  label,
  placeholder,
  disabled = false,
  error,
  compact = false,
}: ResumeStyleSelectorProps) {
  const { t } = useI18n();
  const resolvedPlaceholder = placeholder ?? t('resumeStyles.selectStyle');
  const localizedOptions: StyleOption[] = STYLE_OPTIONS.map((o) => ({
    ...o,
    label: t(`resumeStyles.${o.value}`),
    description: t(o.description),
  }));
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const isReadOnly = !onChange;
  const selectedOption = localizedOptions.find((o) => o.value === value);

  const close = useCallback(() => {
    setIsOpen(false);
    setFocusedIndex(-1);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        close();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [close]);

  useEffect(() => {
    if (isOpen && focusedIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll('[data-style-item]');
      items[focusedIndex]?.scrollIntoView({ block: 'nearest' });
    }
  }, [focusedIndex, isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;

    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (isOpen && focusedIndex >= 0) {
          onChange?.(STYLE_OPTIONS[focusedIndex].value);
          close();
          triggerRef.current?.focus();
        } else {
          setIsOpen(true);
          setFocusedIndex(selectedOption ? STYLE_OPTIONS.findIndex((o) => o.value === selectedOption.value) : 0);
        }
        break;
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        } else {
          setFocusedIndex((prev) => (prev < STYLE_OPTIONS.length - 1 ? prev + 1 : 0));
        }
        break;
      case 'ArrowUp':
        e.preventDefault();
        if (isOpen) {
          setFocusedIndex((prev) => (prev > 0 ? prev - 1 : STYLE_OPTIONS.length - 1));
        }
        break;
      case 'Escape':
        close();
        triggerRef.current?.focus();
        break;
    }
  };

  const handleSelect = (option: StyleOption) => {
    onChange?.(option.value);
    close();
    triggerRef.current?.focus();
  };

  return (
    <div className="w-full" ref={containerRef}>
      {label && (
        <label className="block text-sm font-medium text-text-secondary mb-1.5">
          {label}
        </label>
      )}

      <button
        ref={triggerRef}
        type="button"
        disabled={disabled}
        onClick={() => {
          if (!disabled && !isReadOnly) {
            setIsOpen(!isOpen);
            if (!isOpen) {
              setFocusedIndex(selectedOption ? STYLE_OPTIONS.findIndex((o) => o.value === selectedOption.value) : 0);
            }
          }
        }}
        onKeyDown={handleKeyDown}
        className={clsx(
          'w-full flex items-center gap-3 bg-surface-card border rounded-[10px] transition-all duration-150 text-left',
          compact ? 'px-3 py-2.5' : 'px-4 py-3',
          isOpen
            ? 'border-border-active shadow-[0_0_0_2px_rgba(184,200,232,0.15)]'
            : 'border-border-default hover:bg-surface-hover',
          error && 'border-error',
          (disabled || isReadOnly) && 'opacity-70 cursor-default',
          !disabled && !isReadOnly && 'cursor-pointer',
        )}
        aria-haspopup={isReadOnly ? undefined : 'listbox'}
        aria-expanded={isReadOnly ? undefined : isOpen}
      >
        {selectedOption ? (
          <>
            <span
              className="flex-shrink-0 rounded-full"
              style={{
                width: 10,
                height: 10,
                backgroundColor: selectedOption.color,
              }}
            />
            <span className="text-sm font-medium text-text-primary truncate">
              {selectedOption.label}
            </span>
          </>
        ) : (
          <span className="text-sm text-text-muted">{resolvedPlaceholder}</span>
        )}

        {!isReadOnly && (
          <ChevronDown
            size={16}
            className={clsx(
              'ml-auto flex-shrink-0 text-[#969CA5] transition-transform duration-150',
              isOpen && 'rotate-180',
            )}
          />
        )}
      </button>

      {error && <p className="mt-1 text-xs text-[#D9534F]">{error}</p>}

      {isOpen && (
        <div
          ref={listRef}
          role="listbox"
          className="absolute z-50 mt-1 w-full bg-surface-card border border-border-default rounded-xl shadow-[0_6px_20px_rgba(20,30,40,0.08)] overflow-hidden"
          style={{
            animation: 'fadeSlideIn 120ms ease-out',
          }}
        >
          {localizedOptions.map((option, index) => {
            const isSelected = option.value === value;
            const isFocused = index === focusedIndex;

            return (
              <button
                key={option.value}
                type="button"
                role="option"
                data-style-item
                aria-selected={isSelected}
                onClick={() => handleSelect(option)}
                onMouseEnter={() => setFocusedIndex(index)}
                className={clsx(
                  'w-full flex items-start gap-3 px-4 py-3 text-left transition-colors duration-150',
                  isFocused && !isSelected && 'bg-surface-hover',
                  isSelected && 'bg-accent-primary-muted',
                  !isFocused && !isSelected && 'bg-surface-card',
                )}
              >
                <span
                  className="flex-shrink-0 rounded-full mt-0.5"
                  style={{
                    width: 10,
                    height: 10,
                    backgroundColor: option.color,
                  }}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-text-primary">
                      {option.label}
                    </span>
                    {isSelected && (
                      <Check size={14} className="text-accent-primary flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-[11px] text-text-muted mt-0.5 leading-snug">
                    {option.description}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      )}

    </div>
  );
}

export { STYLE_OPTIONS };
export type { StyleOption };
