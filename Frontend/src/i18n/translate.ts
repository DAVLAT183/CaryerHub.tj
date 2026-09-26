import ru from './locales/ru.json';
import en from './locales/en.json';
import tj from './locales/tj.json';

export type Locale = 'ru' | 'en' | 'tj';

const translations: Record<Locale, Record<string, any>> = { ru, en, tj };
const localeTags: Record<Locale, string> = { ru: 'ru-RU', en: 'en-US', tj: 'tg-TJ' };

let currentLocale: Locale = 'ru';

export function setLocale(locale: Locale): void {
  currentLocale = locale;
  if (typeof document !== 'undefined') {
    document.documentElement.lang = locale;
  }
}

export function getLocale(): Locale {
  return currentLocale;
}

export function getLocaleTag(): string {
  return localeTags[currentLocale];
}

export function initLocaleFromStorage(): void {
  if (typeof window === 'undefined') return;
  const saved = localStorage.getItem('locale') as Locale | null;
  if (saved && ['ru', 'en', 'tj'].includes(saved)) {
    currentLocale = saved;
    document.documentElement.lang = saved;
  }
}

function getNested(obj: any, path: string): any {
  return path.split('.').reduce((current, key) => current?.[key], obj);
}

export function translate(key: string, params?: Record<string, string | number>): string {
  let value = getNested(translations[currentLocale], key);
  if (value === undefined || value === null) {
    value = getNested(translations.ru, key);
  }
  if (value === undefined || value === null) return key;
  if (typeof value !== 'string') return key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      value = value.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
    }
  }
  return value;
}

export const t = translate;
