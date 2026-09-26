'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Briefcase, Building2, GraduationCap, ArrowRight, Terminal, Binary, Sparkles, Bot, TrendingUp, Target, Code, Palette, BarChart3, FileText, PieChart, Users, Smartphone, Shield } from 'lucide-react';
import api from '@/lib/api';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { useI18n } from '@/i18n/I18nContext';
import { formatVacancyWord } from '@/lib/utils';
import type { Category } from '@/types';

const categoryIcons: Record<string, React.ReactNode> = {
  programming: <Code size={20} className="text-text-muted" />,
  design: <Palette size={20} className="text-text-muted" />,
  marketing: <TrendingUp size={20} className="text-text-muted" />,
  copywriting: <FileText size={20} className="text-text-muted" />,
  analytics: <BarChart3 size={20} className="text-text-muted" />,
  management: <Users size={20} className="text-text-muted" />,
  smm: <Smartphone size={20} className="text-text-muted" />,
  testing: <Shield size={20} className="text-text-muted" />,
};

export default function HomePage() {
  const { t } = useI18n();
  const [categories, setCategories] = useState<Category[]>([]);

  const stats = [
    { icon: Briefcase, value: '1 200+', label: t('home.statVacancies') },
    { icon: Building2, value: '500+', label: t('home.statCompanies') },
    { icon: GraduationCap, value: '0', label: t('home.statNoExperience') },
  ];

  useEffect(() => {
    api.get('/categories/').then((res) => {
      const data = res.data;
      setCategories(data.results || data);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  return (
    <div className="min-h-screen bg-bg-primary relative overflow-hidden">
      {/* BACKGROUND GRADIENTS */}
      <div className="absolute inset-0 -z-20 bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary" />
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-accent-primary/5 rounded-full blur-3xl animate-pulse" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent-cyan/5 rounded-full blur-3xl animate-pulse delay-1000" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-accent-primary/3 via-transparent to-accent-cyan/3 rounded-full blur-3xl" />

      {/* HERO SECTION */}
      <section className="relative py-16 sm:py-24 lg:py-32 border-b border-border-default/50">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6">
          <div className="max-w-3xl relative z-10">
            <div className="inline-flex items-center gap-2 bg-gradient-to-r from-accent-primary/10 to-accent-cyan/10 border border-accent-primary/20 px-4 py-2 mb-8 rounded-lg">
              <Terminal size={14} className="text-accent-primary" />
              <span className="text-xs font-mono text-accent-primary uppercase tracking-[3px]">{t('home.platformBadge')}</span>
            </div>

            <h1 className="font-heading text-4xl md:text-5xl lg:text-6xl leading-[1.1] text-text-primary mb-6 font-semibold bg-gradient-to-r from-text-primary via-accent-primary to-accent-cyan bg-clip-text text-transparent">
              <span className="block">{t('home.heroLine1')}</span>
              <span className="block">{t('home.heroLine2')}</span>
              <span className="block mt-2">{t('home.heroLine3')}</span>
            </h1>

            <p className="text-sm text-text-muted mb-10 max-w-lg font-mono border-l-2 border-accent-primary pl-4">
              {t('home.heroDesc')}
            </p>

            <div className="flex flex-col sm:flex-row items-start gap-4">
              <Link href="/jobs">
                <Button size="lg" className="font-mono uppercase tracking-wider bg-gradient-to-r from-accent-primary to-accent-cyan hover:from-accent-primary-hover hover:to-accent-primary shadow-[0_4px_20px_rgba(16,185,129,0.3)]">
                  <Terminal size={16} className="mr-2" />
                  {t('home.viewJobs')}
                  <ArrowRight size={16} className="ml-2" />
                </Button>
              </Link>
              <Link href="/auth/register">
                <Button variant="secondary" size="lg" className="font-mono uppercase tracking-wider border-border-default text-text-secondary hover:border-border-hover hover:text-text-primary">
                  {t('home.createProfile')}
                </Button>
              </Link>
            </div>
          </div>

          {/* HERO IMAGE / ILLUSTRATION */}
          <div className="mt-16 lg:mt-0 lg:absolute lg:right-0 lg:top-1/2 lg:-translate-y-1/2 lg:w-1/2 hidden lg:block relative z-10">
            <div className="relative aspect-square max-w-md mx-auto">
              <div className="absolute inset-0 bg-gradient-to-br from-accent-primary/20 via-transparent to-accent-cyan/20 rounded-[50%] blur-2xl" />
              <div className="relative w-full h-full rounded-[50%] border border-border-default/50 overflow-hidden">
                <img
                  src="https://images.unsplash.com/photo-1521737711867-e3b97375f902?w=600&h=600&fit=crop&crop=center"
                  alt={t('home.heroImgAlt')}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-bg-primary/80 via-transparent to-transparent" />
                <div className="absolute bottom-8 left-8 right-8 text-center">
                  <h3 className="font-heading text-xl text-text-primary mb-2 drop-shadow-lg">{t('home.thousandsVacancies')}</h3>
                  <p className="text-text-muted text-sm drop-shadow-lg">{t('home.forStudents')}</p>
                </div>
              </div>
              <div className="absolute -bottom-6 -right-6 w-24 h-24 bg-gradient-to-br from-accent-cyan to-accent-primary rounded-xl opacity-50 blur-xl" />
              <div className="absolute -top-6 -left-6 w-16 h-16 bg-accent-primary/20 rounded-xl blur-xl" />
            </div>
          </div>

          {/* STATS */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-16 max-w-3xl relative z-10">
            {stats.map((stat, i) => (
              <Card key={stat.label} className="p-6 text-center border-border-default hover:border-border-hover hover:bg-surface-hover transition-all duration-300 group relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-accent-primary/5 to-accent-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <stat.icon size={24} className="text-accent-primary mx-auto mb-3 relative z-10 group-hover:scale-110 transition-transform duration-300" />
                <div className="font-heading text-2xl md:text-3xl text-text-primary mb-1 relative z-10">{stat.value}</div>
                <div className="text-xs text-text-muted font-mono tracking-wider uppercase relative z-10">{stat.label}</div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES SECTION */}
      <section className="py-12 sm:py-20 border-b border-border-default">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-accent-primary/10 border border-accent-primary/20 px-4 py-2 mb-6 rounded-lg">
              <Sparkles size={14} className="text-accent-primary" />
              <span className="text-xs font-mono text-accent-primary uppercase tracking-[3px]">{t('home.whyBadge')}</span>
            </div>
            <h2 className="font-heading text-3xl md:text-4xl text-text-primary mb-4 font-semibold">
              {t('home.whyTitle')} <span className="text-accent-primary">{t('home.whyTitleAccent')}</span>
            </h2>
            <p className="text-text-muted max-w-2xl mx-auto">{t('home.whyDesc')}</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="p-6 border-border-default hover:border-border-hover hover:bg-surface-hover transition-all duration-300 group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-accent-primary/5 to-accent-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-primary to-accent-cyan flex items-center justify-center mb-4 relative z-10 group-hover:scale-110 transition-transform duration-300">
                <Bot size={24} className="text-white" />
              </div>
              <h3 className="font-heading text-lg text-text-primary mb-2 relative z-10">{t('home.feature1Title')}</h3>
              <p className="text-text-muted text-sm relative z-10">{t('home.feature1Desc')}</p>
            </Card>

            <Card className="p-6 border-border-default hover:border-border-hover hover:bg-surface-hover transition-all duration-300 group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-accent-primary/5 to-accent-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-cyan to-accent-primary flex items-center justify-center mb-4 relative z-10 group-hover:scale-110 transition-transform duration-300">
                <Target size={24} className="text-white" />
              </div>
              <h3 className="font-heading text-lg text-text-primary mb-2 relative z-10">{t('home.feature2Title')}</h3>
              <p className="text-text-muted text-sm relative z-10">{t('home.feature2Desc')}</p>
            </Card>

            <Card className="p-6 border-border-default hover:border-border-hover hover:bg-surface-hover transition-all duration-300 group relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-accent-primary/5 to-accent-cyan/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-accent-primary to-accent-cyan flex items-center justify-center mb-4 relative z-10 group-hover:scale-110 transition-transform duration-300">
                <TrendingUp size={24} className="text-white" />
              </div>
              <h3 className="font-heading text-lg text-text-primary mb-2 relative z-10">{t('home.feature3Title')}</h3>
              <p className="text-text-muted text-sm relative z-10">{t('home.feature3Desc')}</p>
            </Card>
          </div>
        </div>
      </section>

      {/* CATEGORIES */}
      <section className="py-12 sm:py-20 border-b border-border-default">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6">
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-2 h-2 bg-accent-primary rounded-full" />
              <h2 className="font-heading text-xl md:text-2xl text-text-primary font-semibold">
                {t('home.categoriesTitle')}
              </h2>
              <div className="flex-1 h-px bg-border-default" />
              <span className="text-xs font-mono text-text-subtle">[ {categories.length} ]</span>
            </div>
            <p className="text-xs text-text-muted font-mono uppercase tracking-[3px] ml-0">{t('home.categoriesSubtitle')}</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {categories.map((cat) => (
              <Link key={cat.id} href={`/jobs?category=${cat.id}`}>
                <Card className="p-5 border-border-default hover:border-border-hover hover:bg-surface-hover transition-all duration-200 group relative overflow-hidden">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-surface-hover border border-border-default flex items-center justify-center flex-shrink-0 group-hover:border-border-hover transition-colors">
                      {categoryIcons[cat.slug] || <Briefcase size={20} className="text-text-muted" />}
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-medium text-text-primary truncate">{cat.name}</div>
                      <div className="text-[11px] text-text-muted mt-0.5">
                        {t('jobs.foundCount', { count: cat.jobs_count ?? 0, word: formatVacancyWord(cat.jobs_count ?? 0) })}
                      </div>
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA SECTION */}
      <section className="py-16 sm:py-24 relative">
        <div className="max-w-[1280px] mx-auto px-4 sm:px-6 text-center relative z-10">
          <div className="absolute inset-0 -z-10 bg-gradient-to-r from-accent-primary/10 via-transparent to-accent-cyan/10 rounded-3xl blur-3xl mx-4" />
          
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-red-500/10 to-accent-primary/10 border border-red-500/20 px-4 py-2 mb-6 rounded-lg">
            <span className="text-xs font-mono text-red-500 uppercase tracking-[3px]">{t('home.ctaBadge')}</span>
          </div>

          <h2 className="font-heading text-2xl md:text-3xl lg:text-4xl text-text-primary mb-4 font-semibold bg-gradient-to-r from-text-primary via-accent-primary to-accent-cyan bg-clip-text text-transparent">
            <span className="block">{t('home.ctaLine1')}</span>
            <span className="block">{t('home.ctaLine2')}</span>
          </h2>

          <p className="text-xs text-text-muted font-mono mb-8 max-w-md mx-auto uppercase tracking-wider border-l-2 border-accent-primary pl-4">
            {t('home.ctaDesc')}
          </p>

          <Link href="/auth/register">
            <Button size="lg" className="font-mono uppercase tracking-wider bg-gradient-to-r from-accent-primary to-accent-cyan hover:from-accent-primary-hover hover:to-accent-primary shadow-[0_4px_20px_rgba(16,185,129,0.3)]">
              <Binary size={16} className="mr-2" />
              {t('home.ctaButton')}
              <ArrowRight size={16} className="ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* SYSTEM BAR */}
      <div className="border-t border-border-default bg-bg-secondary py-3 sm:py-4 px-4 sm:px-6">
        <div className="max-w-[1280px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-accent-primary rounded-full animate-pulse" />
            <span className="text-xs font-mono text-accent-primary uppercase tracking-[2px]">SYSTEM://ONLINE</span>
          </div>
          <div className="hidden md:flex items-center gap-6">
            <span className="text-xs font-mono text-text-subtle">MEM: 42.0GB</span>
            <span className="text-xs font-mono text-text-subtle">CPU: 69%</span>
            <span className="text-xs font-mono text-accent-primary">PING: 42ms</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-accent-primary">CONNECTED</span>
          </div>
        </div>
      </div>
    </div>
  );
}
