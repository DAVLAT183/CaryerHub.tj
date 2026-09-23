import { translate, getLocaleTag, getLocale } from '@/i18n/translate';

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return translate('time.justNow');
  if (diffMins < 60) return translate('time.minutesAgo', { n: diffMins });
  if (diffHours < 24) return translate('time.hoursAgo', { n: diffHours });
  if (diffDays < 7) return translate('time.daysAgo', { n: diffDays });

  return date.toLocaleDateString(getLocaleTag(), {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export function formatSalary(min: number | null, max: number | null): string {
  if (!min && !max) return translate('salary.notSpecified');
  const tag = getLocaleTag();
  if (min && max) return `${min.toLocaleString(tag)} – ${max.toLocaleString(tag)} ₽`;
  if (min) return translate('salary.from', { n: min.toLocaleString(tag) });
  return translate('salary.to', { n: max!.toLocaleString(tag) });
}

export function formatSchedule(schedule: string): string {
  const key = `schedule.${schedule}`;
  const translated = translate(key);
  return translated === key ? schedule : translated;
}

export function formatWorkFormat(format: string): string {
  const key = `workFormat.${format}`;
  const translated = translate(key);
  return translated === key ? format : translated;
}

export function formatResumeStyle(style: string): string {
  const key = `resumeStyles.${style}`;
  const translated = translate(key);
  return translated === key ? style : translated;
}

export function formatStatus(status: string): string {
  const key = `applications.status.${status}`;
  const translated = translate(key);
  return translated === key ? status : translated;
}

export function formatVacancyWord(count: number): string {
  const locale = getLocale();
  if (locale === 'en') return count === 1 ? translate('jobs.vacancyOne') : translate('jobs.vacancyMany');
  const lastTwo = count % 100;
  const lastOne = count % 10;
  if (lastTwo >= 11 && lastTwo <= 19) return translate('jobs.vacancyMany');
  if (lastOne === 1) return translate('jobs.vacancyOne');
  if (lastOne >= 2 && lastOne <= 4) return translate('jobs.vacancyFew');
  return translate('jobs.vacancyMany');
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function clsx(...args: any[]): string {
  const result: string[] = [];
  for (const arg of args) {
    if (!arg) continue;
    if (typeof arg === 'string') {
      result.push(arg);
    } else if (typeof arg === 'object' && !Array.isArray(arg)) {
      for (const [key, value] of Object.entries(arg)) {
        if (value) result.push(key);
      }
    }
  }
  return result.join(' ');
}

const MEDIA_URL = process.env.NEXT_PUBLIC_MEDIA_URL || 'http://localhost:8000/media';

export function mediaUrl(path: string | null | undefined): string | undefined {
  if (!path) return undefined;
  if (path.startsWith('http')) return path;
  return `${MEDIA_URL}${path.startsWith('/') ? '' : '/'}${path}`;
}

let toastContainer: HTMLDivElement | null = null;

export function showToast(message: string, type: 'success' | 'error' | 'info' = 'info') {
  if (typeof window === 'undefined') return;

  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.style.cssText = 'position:fixed;top:80px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const colors = {
    success: 'border-success/30 bg-success/10 text-success',
    error: 'border-error/30 bg-error/10 text-error',
    info: 'border-accent/30 bg-accent/10 text-accent',
  };
  toast.className = `px-4 py-3 rounded-btn text-sm font-medium border backdrop-blur-sm animate-fade-in ${colors[type]}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

export function getErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const err = error as { response?: { status?: number; data?: unknown } };

    if (err.response?.status) {
      const status = err.response.status;
      if (status === 401) return translate('errors.unauthorized');
      if (status === 403) return translate('errors.forbidden');
      if (status === 404) return translate('errors.notFound');
      if (status >= 500) return translate('errors.server');
    }

    const data = err.response?.data;
    if (data && typeof data === 'object' && !(data instanceof Blob)) {
      const obj = data as Record<string, unknown>;
      if ('detail' in obj) return String(obj.detail);
      if ('non_field_errors' in obj) return String(Array.isArray(obj.non_field_errors) ? obj.non_field_errors[0] : obj.non_field_errors);
      const firstKey = Object.keys(obj)[0];
      if (firstKey) {
        const val = obj[firstKey];
        return Array.isArray(val) ? String(val[0]) : String(val);
      }
    }
  }
  return translate('errors.generic');
}
