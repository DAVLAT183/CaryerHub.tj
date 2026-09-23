'use client';

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { setLocale as setGlobalLocale, translate, initLocaleFromStorage, Locale } from './translate';

export type { Locale };

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export function I18nProvider({ children, defaultLocale = 'ru' }: { children: ReactNode; defaultLocale?: Locale }) {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    initLocaleFromStorage();
    const savedLocale = localStorage.getItem('locale') as Locale | null;
    if (savedLocale && ['ru', 'en', 'tj'].includes(savedLocale)) {
      setGlobalLocale(savedLocale);
      setLocaleState(savedLocale);
    } else {
      setGlobalLocale(defaultLocale);
    }
    setLoaded(true);
  }, []);

  useEffect(() => {
    if (loaded) {
      localStorage.setItem('locale', locale);
      setGlobalLocale(locale);
    }
  }, [locale, loaded]);

  const setLocale = useCallback((newLocale: Locale) => {
    setGlobalLocale(newLocale);
    setLocaleState(newLocale);
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>): string => translate(key, params),
    [locale]
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return context;
}
