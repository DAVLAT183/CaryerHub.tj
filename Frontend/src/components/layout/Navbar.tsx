'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X, ChevronDown, Briefcase, Building2, User, LogOut, Plus, Heart, Clock, MessageSquare, Settings, Bell, Sun, Moon, Globe, FileText } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/i18n/ThemeContext';
import { useI18n } from '@/i18n/I18nContext';
import { useNotifications } from '@/hooks/useNotifications';
import Avatar from '@/components/ui/Avatar';
import { clsx } from '@/lib/utils';

const navLinks = [
  { href: '/jobs', labelKey: 'nav.jobs', icon: Briefcase },
  { href: '/companies', labelKey: 'nav.companies', icon: Building2 },
  { href: '/chat', labelKey: 'nav.chat', icon: MessageSquare },
];

const userLinks = (role: string) => [
  { href: role === 'employer' ? '/profile/employer' : '/profile/student', labelKey: 'nav.profile', icon: User },
  { href: '/chat', labelKey: 'nav.chat', icon: MessageSquare },
  { href: '/favorites', labelKey: 'nav.favorites', icon: Heart },
  { href: '/applications', labelKey: 'nav.applications', icon: Clock },
  { href: '/notifications', labelKey: 'nav.notifications', icon: Bell },
  { href: '/settings', labelKey: 'nav.settings', icon: Settings },
];

const languages = [
  { code: 'ru' as const, label: 'RU', flag: '🇷🇺' },
  { code: 'tj' as const, label: 'TJ', flag: '🇹🇯' },
  { code: 'en' as const, label: 'EN', flag: '🇬🇧' },
];

export default function Navbar() {
  const { user, logout, loading } = useAuth();
  const { resolvedTheme, toggleTheme } = useTheme();
  const { locale, setLocale, t } = useI18n();
  const { unreadCount } = useNotifications(!!user);
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);

  useEffect(() => {
    const handleClick = () => { setLangOpen(false); setProfileOpen(false); };
    if (langOpen || profileOpen) {
      document.addEventListener('click', handleClick);
      return () => document.removeEventListener('click', handleClick);
    }
  }, [langOpen, profileOpen]);

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + '/');
  const currentUserLinks = user ? userLinks(user.role) : [];
  const currentLang = languages.find((l) => l.code === locale) || languages[0];

  return (
    <nav className="fixed top-0 left-0 right-0 z-[200] h-16 border-b border-border-default bg-bg-primary/80 backdrop-blur-md">
      <div className="max-w-[1440px] mx-auto h-full px-4 sm:px-6 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group" aria-label="CareerHub">
          <div className="w-9 h-9 rounded-lg bg-accent-primary flex items-center justify-center">
            <Briefcase className="text-text-on-accent" size={18} />
          </div>
          <span className="font-heading text-heading-md text-text-primary tracking-tight font-semibold">CareerHub</span>
        </Link>

        <div className="hidden lg:flex items-center gap-1">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-lg font-body text-label text-text-muted transition-all duration-150',
                isActive(link.href)
                  ? 'text-text-primary bg-surface-hover border border-border-hover'
                  : 'hover:text-text-primary hover:bg-surface-hover'
              )}
            >
              <link.icon size={16} className={clsx('transition-colors', isActive(link.href) && 'text-accent-primary')} />
              {t(link.labelKey)}
            </Link>
          ))}
          {user?.role === 'student' && (
            <Link
              href="/profile/student"
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-[13px] font-medium bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/15 transition-colors"
            >
              <FileText size={14} />
              {t('profile.createResume')}
            </Link>
          )}
        </div>

        <div className="hidden lg:flex items-center gap-1.5">
          {loading ? (
            <div className="w-20 h-10 rounded-lg bg-surface-hover animate-pulse" />
          ) : user ? (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); toggleTheme(); }}
                className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-hover transition-all"
                title={resolvedTheme === 'dark' ? t('theme.light') : t('theme.dark')}
              >
                {resolvedTheme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
              </button>

              <div className="relative">
                <button
                  onClick={(e) => { e.stopPropagation(); setLangOpen(!langOpen); setProfileOpen(false); }}
                  className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-hover transition-all text-xs font-semibold"
                >
                  <Globe size={15} />
                  <span>{currentLang.label}</span>
                  <ChevronDown size={12} className={clsx('transition-transform', langOpen && 'rotate-180')} />
                </button>
                {langOpen && (
                  <div className="absolute right-0 top-full mt-2 w-36 card overflow-hidden animate-fade-in shadow-lg z-50" onClick={(e) => e.stopPropagation()}>
                    {languages.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => { setLocale(lang.code); setLangOpen(false); }}
                        className={clsx(
                          'w-full flex items-center gap-2.5 px-4 py-2.5 text-sm font-medium transition-colors',
                          locale === lang.code
                            ? 'text-accent-primary bg-accent-primary/10'
                            : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                        )}
                      >
                        <span className="text-base">{lang.flag}</span>
                        {lang.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <Link
                href="/notifications"
                className={clsx(
                  'relative p-2 rounded-lg transition-all duration-150',
                  pathname === '/notifications'
                    ? 'text-accent-primary bg-surface-hover'
                    : 'text-text-muted hover:text-text-primary hover:bg-surface-hover'
                )}
              >
                <Bell size={18} />
                {unreadCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 w-5 h-5 rounded-full bg-accent-primary text-[10px] font-bold text-text-on-accent flex items-center justify-center">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </Link>

              <div className="relative">
                <button
                  onClick={(e) => { e.stopPropagation(); setProfileOpen(!profileOpen); }}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-surface-hover transition-all duration-150"
                >
                  <Avatar src={user.avatar} alt={user.username} size="sm" />
                  <span className="font-body text-body-sm text-text-secondary hidden sm:block">{user.username}</span>
                  <ChevronDown size={14} className={clsx('text-text-muted transition-transform duration-150', profileOpen && 'rotate-180')} />
                </button>
                {profileOpen && (
                  <div className="absolute right-0 top-full mt-2 w-56 card overflow-hidden animate-fade-in shadow-lg z-50" role="menu" onClick={(e) => e.stopPropagation()}>
                    <div className="px-4 py-3 border-b border-border-default bg-surface-hover">
                      <span className="font-body text-label text-text-muted">{user.role === 'employer' ? t('auth.roleEmployer') : t('auth.roleStudent')}</span>
                    </div>
                    {currentUserLinks.map((link) => (
                      <Link
                        key={link.href}
                        href={link.href}
                        className="flex items-center gap-2.5 px-4 py-2.5 font-body text-body-sm text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors duration-150"
                        role="menuitem"
                        onClick={() => setProfileOpen(false)}
                      >
                        <link.icon size={16} className="text-text-muted" />
                        {t(link.labelKey)}
                      </Link>
                    ))}
                    <hr className="border-border-default my-2" />
                    <button
                      onClick={() => { setProfileOpen(false); logout(); }}
                      className="w-full flex items-center gap-2.5 px-4 py-2.5 font-body text-body-sm text-error hover:bg-surface-hover transition-colors duration-150 text-left"
                      role="menuitem"
                    >
                      <LogOut size={16} />
                      {t('nav.logout')}
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); toggleTheme(); }}
                className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-hover transition-all"
                title={resolvedTheme === 'dark' ? t('theme.light') : t('theme.dark')}
              >
                {resolvedTheme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
              </button>

              <div className="relative">
                <button
                  onClick={(e) => { e.stopPropagation(); setLangOpen(!langOpen); }}
                  className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-hover transition-all text-xs font-semibold"
                >
                  <Globe size={15} />
                  <span>{currentLang.label}</span>
                  <ChevronDown size={12} className={clsx('transition-transform', langOpen && 'rotate-180')} />
                </button>
                {langOpen && (
                  <div className="absolute right-0 top-full mt-2 w-36 card overflow-hidden animate-fade-in shadow-lg z-50" onClick={(e) => e.stopPropagation()}>
                    {languages.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => { setLocale(lang.code); setLangOpen(false); }}
                        className={clsx(
                          'w-full flex items-center gap-2.5 px-4 py-2.5 text-sm font-medium transition-colors',
                          locale === lang.code
                            ? 'text-accent-primary bg-accent-primary/10'
                            : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                        )}
                      >
                        <span className="text-base">{lang.flag}</span>
                        {lang.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <Link href="/auth/login" className="btn-ghost text-body-sm">{t('nav.login')}</Link>
              <Link href="/auth/register" className="btn-primary text-body-sm">
                <Plus size={16} />
                {t('nav.register')}
              </Link>
            </>
          )}
        </div>

        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="lg:hidden btn-icon"
          aria-label={mobileOpen ? 'Закрыть меню' : 'Открыть меню'}
        >
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {mobileOpen && (
        <div className="lg:hidden border-t border-border-default bg-bg-primary animate-slide-down animate-fade-in">
          <div className="px-4 sm:px-6 py-4 space-y-1">
            <div className="flex items-center gap-2 mb-3">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-hover transition-all"
              >
                {resolvedTheme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
              </button>
              <div className="flex gap-1 p-1 rounded-lg bg-surface-hover">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => setLocale(lang.code)}
                    className={clsx(
                      'px-2.5 py-1 rounded-md text-xs font-semibold transition-colors',
                      locale === lang.code
                        ? 'bg-accent-primary text-white'
                        : 'text-text-muted hover:text-text-primary'
                    )}
                  >
                    {lang.label}
                  </button>
                ))}
              </div>
            </div>

            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className={clsx(
                  'flex items-center gap-3 px-4 py-3 rounded-lg font-body text-body-md transition-colors duration-150',
                  isActive(link.href)
                    ? 'text-text-primary bg-surface-hover border border-border-hover'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'
                )}
              >
                <link.icon size={20} className={clsx('transition-colors', isActive(link.href) && 'text-accent-primary')} />
                {t(link.labelKey)}
              </Link>
            ))}
            {user?.role === 'student' && (
              <Link
                href="/profile/student"
                onClick={() => setMobileOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-lg font-body text-body-md text-accent-primary bg-accent-primary/10 hover:bg-accent-primary/15 transition-colors"
              >
                <FileText size={20} />
                {t('profile.createResume')}
              </Link>
            )}
            <hr className="border-border-default my-3" />
            {user ? (
              <>
                {currentUserLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileOpen(false)}
                    className="flex items-center gap-3 px-4 py-3 rounded-lg font-body text-body-md text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors duration-150"
                  >
                    <link.icon size={20} className="text-text-muted" />
                    {t(link.labelKey)}
                  </Link>
                ))}
                <hr className="border-border-default my-3" />
                <button
                  onClick={() => { setMobileOpen(false); logout(); }}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-lg font-body text-body-md text-error hover:bg-surface-hover transition-colors duration-150 text-left"
                >
                  <LogOut size={20} />
                  {t('nav.logout')}
                </button>
              </>
            ) : (
              <div className="flex flex-col gap-2 pt-2">
                <Link href="/auth/login" onClick={() => setMobileOpen(false)} className="btn-secondary text-body-md justify-center">{t('nav.login')}</Link>
                <Link href="/auth/register" onClick={() => setMobileOpen(false)} className="btn-primary text-body-md justify-center">
                  <Plus size={18} />
                  {t('nav.register')}
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
