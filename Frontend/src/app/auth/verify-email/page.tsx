'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle, XCircle, Loader2, Mail } from 'lucide-react';
import api, { setEmailVerified } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const emailParam = searchParams.get('email');
  const from = searchParams.get('from') || '/jobs';
  const router = useRouter();
  const { user, logout, loading: authLoading } = useAuth();
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'idle'>('loading');
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [code, setCode] = useState('');
  const [codeLoading, setCodeLoading] = useState(false);
  const [codeError, setCodeError] = useState('');
  const [devCode, setDevCode] = useState('');

  useEffect(() => {
    if (emailParam) setEmail(emailParam);
    else if (user?.email) setEmail(user.email);
  }, [emailParam, user]);

  useEffect(() => {
    if (token) {
      verifyToken(token);
      return;
    }

    const checkStatus = async () => {
      if (!localStorage.getItem('access_token')) {
        setStatus('idle');
        return;
      }
      try {
        const res = await api.get('/auth/check-verification/');
        if (res.data.is_email_verified) {
          setEmailVerified(true);
          router.replace(from);
        } else {
          setStatus('idle');
        }
      } catch {
        setStatus('idle');
      }
    };
    checkStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const verifyToken = async (t: string) => {
    try {
      const res = await api.get(`/auth/verify-email/?token=${t}`);
      setEmailVerified(true);
      setStatus('success');
      setMessage(res.data.detail);
    } catch (err: any) {
      setStatus('error');
      setMessage(err.response?.data?.detail?.message || err.response?.data?.detail || 'Ошибка верификации');
    }
  };

  const resendVerification = async () => {
    if (!email && !user) return;
    setResendLoading(true);
    setResendSuccess(false);
    try {
      const res = await api.post('/auth/send-verification/', email ? { email } : {});
      setResendSuccess(true);
      if (res.data?.dev_code) setDevCode(res.data.dev_code);
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Ошибка отправки');
    } finally {
      setResendLoading(false);
    }
  };

  const autoSentRef = useRef(false);
  useEffect(() => {
    if (token || authLoading || !user || autoSentRef.current) return;
    autoSentRef.current = true;
    void resendVerification();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, authLoading, user]);

  const submitCode = async (value?: string) => {
    const nextCode = (value ?? code).trim();
    if (nextCode.length !== 6 || codeLoading) return;
    setCodeLoading(true);
    setCodeError('');
    try {
      await api.post('/auth/verify-code/', { code: nextCode });
      setEmailVerified(true);
      router.replace(from);
    } catch (err: any) {
      setCodeError(
        err.response?.data?.detail?.message ||
          err.response?.data?.detail ||
          'Ошибка проверки кода'
      );
      setCodeLoading(false);
    }
  };

  const onCodeChange = (value: string) => {
    const digits = value.replace(/\D/g, '').slice(0, 6);
    setCode(digits);
    setCodeError('');
    if (digits.length === 6) {
      void submitCode(digits);
    }
  };

  if (token) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center px-6">
        <Card className="max-w-md w-full text-center">
          {status === 'loading' && (
            <>
              <Loader2 size={48} className="text-accent mx-auto mb-4 animate-spin" />
              <h2 className="font-heading font-bold text-xl mb-2">Верификация...</h2>
              <p className="text-muted text-sm">Проверяем ваш email</p>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircle size={48} className="text-green-500 mx-auto mb-4" />
              <h2 className="font-heading font-bold text-xl mb-2">Email верифицирован!</h2>
              <p className="text-muted text-sm mb-6">{message}</p>
              <Button onClick={() => router.replace(from)}>Перейти в приложение</Button>
            </>
          )}

          {status === 'error' && (
            <>
              <XCircle size={48} className="text-error mx-auto mb-4" />
              <h2 className="font-heading font-bold text-xl mb-2">Ошибка верификации</h2>
              <p className="text-muted text-sm mb-6">{message}</p>
              <Link href="/auth/register">
                <Button variant="secondary">Зарегистрироваться заново</Button>
              </Link>
            </>
          )}
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-6">
      <Card className="max-w-md w-full text-center">
        <Mail size={48} className="text-accent mx-auto mb-4" />
        <h2 className="font-heading font-bold text-xl mb-2">Проверьте почту</h2>

        {authLoading ? (
          <div className="py-8">
            <Loader2 size={32} className="text-accent mx-auto animate-spin" />
          </div>
        ) : !user ? (
          <>
            <p className="text-muted text-sm mb-6">
              Войдите в аккаунт, чтобы ввести код подтверждения.
            </p>
            <Link href="/auth/login">
              <Button className="w-full">Войти</Button>
            </Link>
          </>
        ) : (
          <>
            <p className="text-muted text-sm mb-6">
              Мы отправили 6-значный код на{' '}
              <span className="text-text-primary font-medium">{email || user.email}</span>.
              Введите его ниже.
            </p>

            <div className="space-y-4">
              <input
                inputMode="numeric"
                autoComplete="one-time-code"
                maxLength={6}
                value={code}
                onChange={(e) => onCodeChange(e.target.value)}
                placeholder="000000"
                aria-label="Код подтверждения"
                className="input w-full text-center text-2xl font-semibold tracking-[0.4em]"
              />

              {codeError && <p className="text-sm text-red-500">{codeError}</p>}

              <Button
                onClick={() => submitCode()}
                loading={codeLoading}
                disabled={code.length !== 6}
                className="w-full"
              >
                Подтвердить
              </Button>

              <Button
                onClick={resendVerification}
                loading={resendLoading}
                variant="secondary"
                className="w-full"
              >
                Отправить код повторно
              </Button>

              {resendSuccess && (
                <p className="text-sm text-green-500">Письмо отправлено! Проверьте почту.</p>
              )}
              {devCode && (
                <p className="text-sm text-amber-400">
                  SMTP не настроен — код подтверждения:{' '}
                  <span className="font-mono font-bold tracking-[0.2em]">{devCode}</span>
                </p>
              )}
              {!resendSuccess && message && <p className="text-sm text-red-500">{message}</p>}
              <p className="text-xs text-muted">
                Не пришло письмо? Проверьте папку «Спам» или отправьте код повторно.
              </p>
            </div>
          </>
        )}

        <div className="mt-6 pt-4 border-t border-border-default flex items-center justify-center gap-4">
          {user ? (
            <button
              type="button"
              onClick={logout}
              className="text-sm text-muted hover:text-text-primary transition-colors"
            >
              Выйти из аккаунта
            </button>
          ) : (
            <Link href="/auth/login" className="text-sm text-muted hover:text-text-primary transition-colors">
              Вернуться к входу
            </Link>
          )}
        </div>
      </Card>
    </div>
  );
}
