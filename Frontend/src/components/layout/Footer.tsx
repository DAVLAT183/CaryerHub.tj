'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Building2, Twitter, Linkedin, Github, Mail } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useI18n } from '@/i18n/I18nContext';

export default function Footer() {
  const pathname = usePathname();
  const currentYear = new Date().getFullYear();
  const { user } = useAuth();
  const { t } = useI18n();

  if (pathname === '/chat') return null;

  const footerLinks = {
    product: [
      { label: t('nav.jobs'), href: '/jobs' },
      { label: t('nav.companies'), href: '/companies' },
      { label: t('footer.internships'), href: '/jobs?category=internship' },
      { label: t('footer.remoteWork'), href: '/jobs?work_format=remote' },
    ],
    company: [
      { label: t('footer.about'), href: '/about' },
      { label: t('nav.blog'), href: '/blog' },
      { label: t('footer.careers'), href: '/jobs?company=careerhub' },
    ],
    forEmployers: [
      { label: t('footer.postJob'), href: '/employer/create-job' },
      { label: t('footer.findCandidates'), href: '/employer/search' },
      { label: t('footer.pricing'), href: '/pricing' },
    ],
    support: [
      { label: t('footer.help'), href: '/help' },
      { label: t('footer.contact'), href: '/contact' },
      { label: t('footer.privacy'), href: '/privacy' },
      { label: t('footer.terms'), href: '/terms' },
    ],
  };

  const socialLinks = [
    { icon: Twitter, href: 'https://twitter.com', label: 'Twitter' },
    { icon: Linkedin, href: 'https://linkedin.com', label: 'LinkedIn' },
    { icon: Github, href: 'https://github.com', label: 'GitHub' },
    { icon: Mail, href: 'mailto:hello@careerhub.example', label: 'Email' },
  ];

  return (
    <footer className="border-t border-border-default bg-bg-secondary mt-auto">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-8 sm:py-12 lg:py-16">
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8 lg:gap-12 mb-12">
          <div className="col-span-2 lg:col-span-1">
            <Link href="/" className="flex items-center gap-2.5 mb-4" aria-label={`${t('common.appName')} - ${t('footer.home')}`}>
              <img src="/logo.svg" alt={t('common.appName')} className="w-9 h-9 rounded-lg" />
              <span className="font-heading text-heading-md text-text-primary tracking-tight font-semibold">
                CareerHub
              </span>
            </Link>
            <p className="font-body text-body-sm text-text-muted mb-6 max-w-xs">
              {t('footer.tagline')}
            </p>
            <div className="flex gap-3">
              {socialLinks.map((social) => (
                <a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-icon p-2 text-text-muted hover:text-text-primary"
                  aria-label={social.label}
                >
                  <social.icon size={18} />
                </a>
              ))}
            </div>
          </div>

          <nav aria-label={t('footer.product')}>
            <h3 className="section-title mb-4">{t('footer.product')}</h3>
            <ul className="space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="font-body text-body-sm text-text-muted hover:text-text-primary transition-colors duration-150"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          <nav aria-label={t('nav.companies')}>
            <h3 className="section-title mb-4">{t('nav.companies')}</h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="font-body text-body-sm text-text-muted hover:text-text-primary transition-colors duration-150"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {user?.role === 'employer' && (
            <nav aria-label={t('footer.forEmployers')}>
              <h3 className="section-title mb-4">{t('footer.forEmployers')}</h3>
              <ul className="space-y-3">
                {footerLinks.forEmployers.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="font-body text-body-sm text-text-muted hover:text-text-primary transition-colors duration-150"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          )}

          <nav aria-label={t('footer.support')}>
            <h3 className="section-title mb-4">{t('footer.support')}</h3>
            <ul className="space-y-3">
              {footerLinks.support.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="font-body text-body-sm text-text-muted hover:text-text-primary transition-colors duration-150"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="pt-8 border-t border-border-default">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="font-body text-caption text-text-subtle">
              © {currentYear} CareerHub. {t('footer.rights')}.
            </p>
            <div className="flex items-center gap-6">
              <Link
                href="/privacy"
                className="font-body text-caption text-text-subtle hover:text-text-primary transition-colors duration-150"
              >
                {t('footer.privacy')}
              </Link>
              <Link
                href="/terms"
                className="font-body text-caption text-text-subtle hover:text-text-primary transition-colors duration-150"
              >
                {t('footer.terms')}
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}