'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { clsx } from '@/lib/utils';
import { useI18n } from '@/i18n/I18nContext';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value?: string;
  onChange?: (value: string) => void;
  label?: string;
  options: SelectOption[];
  placeholder?: string;
  error?: string;
  disabled?: boolean;
  className?: string;
}

export default function Select({
  value,
  onChange,
  label,
  options,
  placeholder,
  error,
  disabled = false,
  className,
}: SelectProps) {
  const { t } = useI18n();
  const resolvedPlaceholder = placeholder ?? t('select.placeholder');
  const [isOpen, setIsOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const isReadOnly = !onChange;
  const selectedOption = options.find((o) => o.value === value);

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
      const items = listRef.current.querySelectorAll('[data-select-item]');
      items[focusedIndex]?.scrollIntoView({ block: 'nearest' });
    }
  }, [focusedIndex, isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled || isReadOnly) return;

    switch (e.key) {
      case 'Enter':
      case ' ':
        e.preventDefault();
        if (isOpen && focusedIndex >= 0) {
          onChange?.(options[focusedIndex].value);
          close();
          triggerRef.current?.focus();
        } else {
          setIsOpen(true);
          setFocusedIndex(selectedOption ? options.findIndex((o) => o.value === selectedOption.value) : 0);
        }
        break;
      case 'ArrowDown':
        e.preventDefault();
        if (!isOpen) {
          setIsOpen(true);
          setFocusedIndex(0);
        } else {
          setFocusedIndex((prev) => (prev < options.length - 1 ? prev + 1 : 0));
        }
        break;
      case 'ArrowUp':
        e.preventDefault();
        if (isOpen) {
          setFocusedIndex((prev) => (prev > 0 ? prev - 1 : options.length - 1));
        }
        break;
      case 'Escape':
        close();
        triggerRef.current?.focus();
        break;
    }
  };

  const handleSelect = (option: SelectOption) => {
    onChange?.(option.value);
    close();
    triggerRef.current?.focus();
  };

  return (
    <div className={clsx('w-full relative', className)} ref={containerRef}>
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
              setFocusedIndex(selectedOption ? options.findIndex((o) => o.value === selectedOption.value) : 0);
            }
          }
        }}
        onKeyDown={handleKeyDown}
        className={clsx(
          'w-full flex items-center gap-3 bg-surface-card border rounded-[10px] transition-all duration-150 text-left',
          'px-4 py-3',
          isOpen
            ? 'border-border-active shadow-[0_0_0_2px_rgba(184,200,232,0.15)]'
            : 'border-border-default hover:bg-surface-hover',
          error && 'border-error',
          (disabled || isReadOnly) && 'opacity-70 cursor-default',
          !disabled && !isReadOnly && 'cursor-pointer',
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        {selectedOption ? (
          <span className="text-sm font-medium text-text-primary truncate">
            {selectedOption.label}
          </span>
        ) : (
          <span className="text-sm text-text-muted">{resolvedPlaceholder}</span>
        )}

        {!isReadOnly && (
          <ChevronDown
            size={16}
            className={clsx(
              'ml-auto flex-shrink-0 text-text-muted transition-transform duration-150',
              isOpen && 'rotate-180',
            )}
          />
        )}
      </button>

      {error && <p className="mt-1 text-xs text-error">{error}</p>}

      {isOpen && (
        <div
          ref={listRef}
          role="listbox"
          className="absolute z-50 mt-1 w-full bg-surface-card border border-border-default rounded-xl shadow-[0_6px_20px_rgba(20,30,40,0.08)] overflow-hidden max-h-60 overflow-y-auto"
          style={{
            animation: 'fadeSlideIn 120ms ease-out',
          }}
        >
          {options.map((option, index) => {
            const isSelected = option.value === value;
            const isFocused = index === focusedIndex;

            return (
              <button
                key={option.value}
                type="button"
                role="option"
                data-select-item
                aria-selected={isSelected}
                onClick={() => handleSelect(option)}
                onMouseEnter={() => setFocusedIndex(index)}
                className={clsx(
                  'w-full flex items-center gap-3 px-4 py-3 text-left transition-colors duration-150',
                  isFocused && !isSelected && 'bg-surface-hover',
                  isSelected && 'bg-accent-primary-muted',
                  !isFocused && !isSelected && 'bg-surface-card',
                )}
              >
                <span className={clsx(
                  'text-sm flex-1 min-w-0 truncate',
                  isSelected ? 'font-medium text-text-primary' : 'text-text-primary',
                )}>
                  {option.label}
                </span>
                {isSelected && (
                  <Check size={14} className="text-accent-primary flex-shrink-0" />
                )}
              </button>
            );
          })}
          {options.length === 0 && (
            <div className="px-4 py-3 text-sm text-text-muted">{t('select.empty')}</div>
          )}
        </div>
      )}
    </div>
  );
}
