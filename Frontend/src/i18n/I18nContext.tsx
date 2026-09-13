'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import ru from './locales/ru.json';
import en from './locales/en.json';
import tj from './locales/tj.json';

type Locale = 'ru' | 'en' | 'tj';

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

const translations: Record<Locale, Record<string, any>> = {
  ru,
  en,
  tj,
};

function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((current, key) => current?.[key], obj);
}

export function I18nProvider({ children, defaultLocale = 'ru' }: { children: ReactNode; defaultLocale?: Locale }) {
  const [locale, setLocaleState] = useState<Locale>(defaultLocale);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const savedLocale = localStorage.getItem('locale') as Locale | null;
    if (savedLocale && ['ru', 'en', 'tj'].includes(savedLocale)) {
      setLocaleState(savedLocale);
    }
    setLoaded(true);
  }, []);

  useEffect(() => {
    if (loaded) {
      localStorage.setItem('locale', locale);
      document.documentElement.lang = locale;
    }
  }, [locale, loaded]);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
  };

  const t = (key: string, params?: Record<string, string | number>): string => {
    const translation = getNestedValue(translations[locale], key);
    if (!translation) {
      return key;
    }
    
    if (params) {
      return Object.entries(params).reduce(
        (str, [key, value]) => str.replace(new RegExp(`\\{${key}\\}`, 'g'), String(value)),
        translation
      );
    }
    
    return translation;
  };

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
