'use client';

import { useState, useEffect } from 'react';
import { Check, Sparkles, Zap, Crown, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import api from '@/lib/api';

const planIcons: Record<string, typeof Zap> = {
  free: Zap,
  professional: Sparkles,
  corporate: Crown,
};

const planPopular: Record<string, boolean> = {
  free: false,
  professional: true,
  corporate: false,
};

interface TariffPlan {
  id: number;
  name: string;
  display_name: string;
  price: number;
  duration_days: number;
  features: string[];
}

export default function PricingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [plans, setPlans] = useState<TariffPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState<number | null>(null);
  const [currentPlan, setCurrentPlan] = useState<string>('free');
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    const status = searchParams.get('status');
    if (status === 'success') {
      setMessage('Оплата прошла успешно! Подписка активирована.');
    } else if (status === 'failed') {
      setMessage('Оплата не была завершена. Попробуйте снова.');
    }
  }, [searchParams]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [plansRes, accessRes] = await Promise.all([
          api.get('/tariffs/'),
          api.get('/payments/check-access/').catch(() => null),
        ]);
        setPlans(plansRes.data.results || plansRes.data);
        if (accessRes?.data?.current_plan) {
          setCurrentPlan(accessRes.data.current_plan);
        }
      } catch {
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handlePurchase = async (plan: TariffPlan) => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/auth/login');
      return;
    }

    setPurchasing(plan.id);
    try {
      const res = await api.post('/payments/create/', { plan_id: plan.id });
      if (res.data.redirect_url) {
        window.location.href = res.data.redirect_url;
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Ошибка при создании платежа';
      setMessage(detail);
    } finally {
      setPurchasing(null);
    }
  };

  const getCtaText = (plan: TariffPlan) => {
    if (plan.name === 'free') return 'Начать бесплатно';
    if (plan.name === currentPlan) return 'Текущий план';
    return 'Купить подписку';
  };

  const getCtaAction = (plan: TariffPlan) => {
    if (plan.name === 'free') return '/auth/register';
    return null;
  };

  if (loading) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-8 sm:py-12 flex items-center justify-center min-h-[60vh]">
        <Loader2 size={32} className="animate-spin text-accent-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-8 sm:py-12">
      <div className="text-center mb-12">
        <h1 className="font-heading font-bold text-3xl md:text-4xl mb-3">Тарифы</h1>
        <p className="text-text-muted text-lg max-w-xl mx-auto">
          Выберите подходящий план для вашей компании. Все планы включают 14-дневный пробный период.
        </p>
      </div>

      {message && (
        <div className={`max-w-xl mx-auto mb-8 p-4 rounded-xl text-sm text-center ${
          message.includes('успешно') ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
        }`}>
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
        {plans.map((plan) => {
          const Icon = planIcons[plan.name] || Zap;
          const isPopular = planPopular[plan.name];
          const isCurrent = plan.name === currentPlan;
          const isPaid = plan.name !== 'free';
          const ctaText = getCtaText(plan);
          const ctaHref = getCtaAction(plan);

          return (
            <div
              key={plan.name}
              className={`card-minimal p-8 relative ${
                isPopular ? 'border-accent-primary shadow-[0_0_30px_rgba(16,185,129,0.15)]' : ''
              } ${isCurrent ? 'ring-2 ring-accent-primary/50' : ''}`}
            >
              {isPopular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-accent-primary text-white text-xs font-bold">
                  Популярный
                </div>
              )}
              {isCurrent && (
                <div className="absolute -top-3 right-4 px-3 py-1 rounded-full bg-blue-500/20 text-blue-400 text-xs font-semibold border border-blue-500/30">
                  Текущий
                </div>
              )}
              <div className="w-12 h-12 rounded-xl bg-accent-primary/10 flex items-center justify-center mb-4">
                <Icon size={22} className="text-accent-primary" />
              </div>
              <h3 className="font-heading font-semibold text-lg">{plan.display_name}</h3>
              <p className="text-sm text-text-muted mb-4">
                {plan.name === 'free' && 'Для начинающих'}
                {plan.name === 'professional' && 'Для растущих компаний'}
                {plan.name === 'corporate' && 'Для крупных компаний'}
              </p>
              <div className="mb-6">
                <span className="text-3xl font-bold">{plan.price}</span>
                <span className="text-sm text-text-muted ml-1">
                  {plan.price === 0 ? 'навсегда' : 'сомони/мес'}
                </span>
              </div>
              <ul className="space-y-3 mb-8">
                {plan.features.map((f: string) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-text-secondary">
                    <Check size={16} className="text-accent-primary mt-0.5 flex-shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>

              {ctaHref ? (
                <Link href={ctaHref}>
                  <button
                    className={`w-full py-3 rounded-xl text-sm font-semibold transition-colors ${
                      isPopular
                        ? 'bg-accent-primary text-white hover:bg-accent-primary-hover'
                        : 'bg-surface-hover text-text-primary border border-border-default hover:border-accent-primary'
                    }`}
                  >
                    {ctaText}
                  </button>
                </Link>
              ) : (
                <button
                  onClick={() => handlePurchase(plan)}
                  disabled={isCurrent || purchasing === plan.id}
                  className={`w-full py-3 rounded-xl text-sm font-semibold transition-colors ${
                    isCurrent
                      ? 'bg-surface-hover text-text-muted border border-border-default cursor-not-allowed'
                      : isPopular
                        ? 'bg-accent-primary text-white hover:bg-accent-primary-hover'
                        : 'bg-surface-hover text-text-primary border border-border-default hover:border-accent-primary'
                  } ${purchasing === plan.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {purchasing === plan.id ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 size={16} className="animate-spin" />
                      Обработка...
                    </span>
                  ) : ctaText}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
