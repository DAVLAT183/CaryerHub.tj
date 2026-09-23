'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, MapPin, Clock, Building2, Globe, CheckCircle, Send, Download, Map, Image as ImageIcon, FileText, MessageSquare, Route, Navigation, Loader2 } from 'lucide-react';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Modal from '@/components/ui/Modal';
import Textarea from '@/components/ui/Textarea';
import Select from '@/components/ui/Select';
import Skeleton from '@/components/ui/Skeleton';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import ReadingProgress from '@/components/ui/ReadingProgress';
import ResumeStyleSelector, { STYLE_OPTIONS } from '@/components/ui/ResumeStyleSelector';
import { formatSalary, formatSchedule, formatWorkFormat, formatResumeStyle, formatDate, showToast, getErrorMessage } from '@/lib/utils';
import type { Job, Resume, ResumeStyle } from '@/types';

type StyleOptionItem = (typeof STYLE_OPTIONS)[number];

const STYLE_OPTIONS_MAP = Object.fromEntries(STYLE_OPTIONS.map((o: StyleOptionItem) => [o.value, o]));

export default function JobDetailPage() {
  const { id } = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [applyOpen, setApplyOpen] = useState(false);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResume, setSelectedResume] = useState('');
  const [coverLetter, setCoverLetter] = useState('');
  const [applying, setApplying] = useState(false);
  const [applied, setApplied] = useState(false);
  const [isFavorited, setIsFavorited] = useState(false);
  const [generatingPdf, setGeneratingPdf] = useState(false);
  const [pdfMenuOpen, setPdfMenuOpen] = useState(false);
  const pdfMenuRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<HTMLDivElement>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeData, setRouteData] = useState<{
    distance_text: string;
    duration_text: string;
    steps: { text: string; distance: number }[];
    polyline: number[][];
    user_address: string;
  } | null>(null);
  const [routeError, setRouteError] = useState('');
  const routeMapRef = useRef<HTMLDivElement>(null);
  const [routeMapLoaded, setRouteMapLoaded] = useState(false);

  useEffect(() => {
    api.get(`/jobs/${id}/`).then((res) => {
      setJob(res.data);
      setIsFavorited(res.data.is_favorited || false);
    }).catch((err) => {
      showToast(getErrorMessage(err), 'error');
    }).finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (user?.role === 'student') {
      api.get('/resumes/').then((res) => {
        const data = res.data;
        setResumes(data.results || data);
      }).catch(() => {});
    }
  }, [user]);

  useEffect(() => {
    if (user?.role === 'student' && job) {
      api.get('/applications/').then((res) => {
        const data = res.data;
        const list = data.results || data;
        const hasApplied = list.some((a: { job: number }) => a.job === job.id);
        setApplied(hasApplied);
      }).catch(() => {});
    }
  }, [user, job]);

  useEffect(() => {
    if (job?.has_location && mapRef.current && !mapLoaded) {
      initMap();
    }
  }, [job, mapLoaded]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (pdfMenuRef.current && !pdfMenuRef.current.contains(e.target as Node)) {
        setPdfMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const initMap = () => {
    if (!mapRef.current || !job?.location_lat || !job?.location_lng) return;

    const lat = Number(job.location_lat);
    const lng = Number(job.location_lng);

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyBFw0Qbyq9zTFTd-tUY6dZWTgaQzuU17R8&callback=initGoogleMap`;
    script.async = true;
    script.defer = true;

    (window as any).initGoogleMap = () => {
      try {
        const map = new (window as any).google.maps.Map(mapRef.current!, {
          center: { lat, lng },
          zoom: 15,
          styles: [
            { elementType: 'geometry', stylers: [{ color: '#1d2c4d' }] },
            { elementType: 'labels.text.fill', stylers: [{ color: '#8ec3b9' }] },
            { elementType: 'labels.text.stroke', stylers: [{ color: '#1a3646' }] },
            { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0e1626' }] },
          ],
          disableDefaultUI: true,
          zoomControl: true,
          mapTypeControl: false,
          streetViewControl: false,
        });

        const marker = new (window as any).google.maps.Marker({
          position: { lat, lng },
          map,
          title: job.title,
          icon: {
            path: (window as any).google.maps.SymbolPath.CIRCLE,
            scale: 10,
            fillColor: '#10B981',
            fillOpacity: 1,
            strokeColor: '#ffffff',
            strokeWeight: 2,
          },
        });

        const infoWindow = new (window as any).google.maps.InfoWindow({
          content: `<div style="padding:8px;font-family:Inter,sans-serif">
            <strong style="font-size:14px">${job.title}</strong><br/>
            <span style="color:#666;font-size:12px">${job.location_address || job.employer?.address || ''}</span>
          </div>`,
        });

        marker.addListener('click', () => infoWindow.open(map, marker));
        infoWindow.open(map, marker);

        setMapLoaded(true);
      } catch (e) {
        console.warn('Google Maps initialization failed:', e);
        setMapLoaded(true);
      }
    };

    document.head.appendChild(script);
  };

  const handleApply = async () => {
    if (!selectedResume) return;
    setApplying(true);
    try {
      await api.post('/applications/', {
        job: job?.id,
        resume: Number(selectedResume),
        cover_letter: coverLetter,
      });
      setApplied(true);
      setApplyOpen(false);
      showToast('Отклик отправлен!', 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setApplying(false);
    }
  };

  const toggleFavorite = async () => {
    if (!job) return;
    try {
      if (isFavorited) {
        await api.delete(`/favorites/${job.id}/remove/`);
        setIsFavorited(false);
        showToast('Удалено из избранного', 'info');
      } else {
        await api.post('/favorites/add/', { job_id: job.id });
        setIsFavorited(true);
        showToast('Добавлено в избранное', 'success');
      }
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const handleDownloadPdf = async (style?: string) => {
    if (!job) return;
    setGeneratingPdf(true);
    setPdfMenuOpen(false);
    try {
      const params: Record<string, string> = {};
      if (style) params.style = style;
      const response = await api.get(`/jobs/${job.id}/pdf/`, { params, responseType: 'blob' });
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const styleNames: Record<string, string> = { classic: 'Классический', modern: 'Современный', minimal: 'Минималистичный', creative: 'Креативный' };
      const styleKey = style || 'modern';
      link.download = `vacancy_${job.id}_${styleNames[styleKey] || 'PDF'}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      showToast('PDF скачан', 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setGeneratingPdf(false);
    }
  };

  const calculateRoute = async () => {
    if (!user?.location || !job) return;
    setRouteLoading(true);
    setRouteError('');
    setRouteData(null);
    try {
      const res = await api.post('/route/', {
        user_location: user.location,
        job_lat: Number(job.location_lat),
        job_lng: Number(job.location_lng),
      });
      setRouteData(res.data);
      setTimeout(() => initRouteMap(res.data.polyline, res.data.user_address), 100);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Не удалось построить маршрут';
      setRouteError(msg);
    } finally {
      setRouteLoading(false);
    }
  };

  const initRouteMap = (polyline: number[][], userAddress: string) => {
    if (!routeMapRef.current || !job?.location_lat || !job?.location_lng) return;
    if (!(window as any).google?.maps) return;

    try {
      const jobLat = Number(job.location_lat);
      const jobLng = Number(job.location_lng);
      const userLat = polyline[0][1];
      const userLng = polyline[0][0];

      const map = new (window as any).google.maps.Map(routeMapRef.current!, {
        center: { lat: (userLat + jobLat) / 2, lng: (userLng + jobLng) / 2 },
        zoom: 12,
        styles: [
          { elementType: 'geometry', stylers: [{ color: '#1d2c4d' }] },
          { elementType: 'labels.text.fill', stylers: [{ color: '#8ec3b9' }] },
          { elementType: 'labels.text.stroke', stylers: [{ color: '#1a3646' }] },
          { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#0e1626' }] },
        ],
        disableDefaultUI: true,
        zoomControl: true,
      });

      const path = polyline.map((coord: number[]) => ({ lat: coord[1], lng: coord[0] }));

      new (window as any).google.maps.Polyline({
        path,
        geodesic: true,
        strokeColor: '#10B981',
        strokeOpacity: 0.9,
        strokeWeight: 4,
        map,
      });

      new (window as any).google.maps.Marker({
        position: { lat: userLat, lng: userLng },
        map,
        title: 'Вы',
        icon: { path: (window as any).google.maps.SymbolPath.CIRCLE, scale: 8, fillColor: '#3B82F6', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 2 },
      });

      new (window as any).google.maps.Marker({
        position: { lat: jobLat, lng: jobLng },
        map,
        title: job.title,
        icon: { path: (window as any).google.maps.SymbolPath.CIRCLE, scale: 8, fillColor: '#10B981', fillOpacity: 1, strokeColor: '#fff', strokeWeight: 2 },
      });

      setRouteMapLoaded(true);
    } catch (e) {
      console.warn('Route map error:', e);
    }
  };

  if (loading) {
    return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Skeleton className="h-6 w-40 mb-6" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
          <div className="lg:col-span-2">
            <Skeleton className="h-8 w-3/4 mb-4" />
            <Skeleton className="h-4 w-1/2 mb-6" />
            <Skeleton className="h-40 w-full rounded-card" />
          </div>
          <div>
            <Skeleton className="h-60 w-full rounded-card" />
          </div>
        </div>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-12 sm:py-16 text-center">
        <div className="text-5xl mb-4">😕</div>
        <h2 className="font-heading font-bold text-xl mb-2">Вакансия не найдена</h2>
        <Link href="/jobs" className="text-accent text-sm hover:text-accent-cyan">← ко всем вакансиям</Link>
      </div>
    );
  }

  return (
    <div className="max-w-[1280px] mx-auto px-6 py-8">
      <ReadingProgress />
      <Breadcrumbs
        items={[
          { label: 'Вакансии', href: '/jobs' },
          { label: job.title },
        ]}
        className="mb-4"
      />
      <Link href="/jobs" className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-white transition-colors mb-4 sm:mb-6">
        <ArrowLeft size={14} />
        Ко всем вакансиям
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-start justify-between mb-2">
            <div className="flex-1">
              <h1 className="font-heading font-bold text-xl sm:text-2xl md:text-3xl">{job.title}</h1>
              <p className="text-muted text-sm mt-1">{job.employer?.company_name || 'Компания'}</p>
            </div>
            <div className="flex items-center gap-2 ml-4">
              {user?.role === 'student' && (
                <button
                  onClick={toggleFavorite}
                  className="p-2 rounded-btn hover:bg-white/5 transition-colors"
                >
                  {isFavorited ? '★' : '☆'}
                </button>
              )}
              <div className="relative" ref={pdfMenuRef}>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setPdfMenuOpen(!pdfMenuOpen)}
                  loading={generatingPdf}
                  className="flex items-center gap-1.5"
                >
                  <FileText size={14} />
                  PDF
                </Button>
                {pdfMenuOpen && (
                  <div className="absolute right-0 top-full mt-1 z-50 w-56 bg-surface-card border border-border-default rounded-xl shadow-[0_6px_20px_rgba(20,30,40,0.08)] overflow-hidden">
                    <p className="px-3 py-2 text-xs text-text-muted font-medium border-b border-border-default">Выберите стиль</p>
                    {STYLE_OPTIONS.map((s: StyleOptionItem) => (
                      <button
                        key={s.value}
                        onClick={() => handleDownloadPdf(s.value)}
                        className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-text-primary hover:bg-surface-hover transition-colors"
                      >
                        <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: s.color }} />
                        {s.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-wrap gap-1.5 sm:gap-2 mb-4 sm:mb-6">
            {(job.salary_min || job.salary_max) && (
              <Badge variant="salary">{formatSalary(job.salary_min, job.salary_max)}</Badge>
            )}
            <Badge variant={job.schedule === 'flexible' ? 'flexible' : 'default'}>
              <Clock size={10} className="mr-1" />
              {formatSchedule(job.schedule)}
            </Badge>
            <Badge variant={job.work_format === 'online' ? 'online' : job.work_format === 'hybrid' ? 'hybrid' : 'offline'}>
              <MapPin size={10} className="mr-1" />
              {formatWorkFormat(job.work_format)}
            </Badge>
            {!job.experience_required && <Badge variant="no-experience">Без опыта</Badge>}
            {job.source === 'somon_tj' && (
              <Badge variant="default" className="bg-accent-primary/10 text-accent-primary border-accent-primary/20">
                <ImageIcon size={10} className="mr-1" />
                somon.tj
              </Badge>
            )}
          </div>

          {job.image_url && (
            <div className="rounded-card overflow-hidden mb-6 border border-border-default">
              <img
                src={job.image_url}
                alt={job.title}
                className="w-full h-64 md:h-80 object-cover"
              />
            </div>
          )}

          <Card className="mb-6">
            <h2 className="font-heading font-semibold text-lg mb-4 flex items-center gap-2">
              <FileText size={18} className="text-accent-primary" />
              Описание вакансии
            </h2>
            <div className="text-sm text-soft/80 leading-relaxed whitespace-pre-wrap">
              {job.description}
            </div>
          </Card>

          {job.has_location && (
            <Card className="mb-6">
              <h2 className="font-heading font-semibold text-lg mb-4 flex items-center gap-2">
                <Map size={18} className="text-accent-primary" />
                Местоположение на карте
              </h2>
              <div className="mb-4">
                <div
                  ref={mapRef}
                  className="h-64 md:h-80 rounded-card bg-surface-hover"
                  style={{ minHeight: '256px' }}
                />
                {job.location_address && (
                  <div className="flex items-center justify-between mt-2">
                    <p className="text-sm text-muted flex items-center gap-1.5">
                      <MapPin size={14} />
                      {job.location_address}
                    </p>
                    <a
                      href={`https://www.google.com/maps?q=${job.location_lat},${job.location_lng}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-accent-primary hover:text-accent-primary/80 flex items-center gap-1"
                    >
                      <Globe size={12} />
                      Открыть в Google Maps
                    </a>
                  </div>
                )}
              </div>
            </Card>
          )}

          {user?.role === 'student' && job.has_location && user.location && (
            <Card className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-heading font-semibold text-lg flex items-center gap-2">
                  <Route size={18} className="text-accent-primary" />
                  Маршрут до работы
                </h2>
                {!routeData && !routeLoading && (
                  <button
                    onClick={calculateRoute}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/20 transition-colors"
                  >
                    <Navigation size={14} />
                    Построить маршрут
                  </button>
                )}
              </div>

              {routeLoading && (
                <div className="flex flex-col items-center py-8">
                  <Loader2 size={32} className="animate-spin text-accent-primary mb-3" />
                  <p className="text-sm text-muted">AI анализирует оптимальный путь...</p>
                </div>
              )}

              {routeError && (
                <div className="p-4 rounded-xl bg-error/10 border border-error/20 text-sm text-error">
                  {routeError}
                </div>
              )}

              {routeData && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 rounded-xl bg-surface-hover border border-border-default text-center">
                      <Navigation size={18} className="text-accent-primary mx-auto mb-1" />
                      <p className="text-lg font-bold text-text-primary">{routeData.distance_text}</p>
                      <p className="text-[11px] text-text-muted">Расстояние</p>
                    </div>
                    <div className="p-3 rounded-xl bg-surface-hover border border-border-default text-center">
                      <Clock size={18} className="text-accent-primary mx-auto mb-1" />
                      <p className="text-lg font-bold text-text-primary">{routeData.duration_text}</p>
                      <p className="text-[11px] text-text-muted">Время в пути</p>
                    </div>
                    <div className="p-3 rounded-xl bg-surface-hover border border-border-default text-center">
                      <MapPin size={18} className="text-accent-primary mx-auto mb-1" />
                      <p className="text-sm font-bold text-text-primary truncate">{routeData.user_address.split(',')[0]}</p>
                      <p className="text-[11px] text-text-muted">Откуда</p>
                    </div>
                  </div>

                  <div
                    ref={routeMapRef}
                    className="h-64 rounded-xl bg-surface-hover"
                    style={{ minHeight: '200px' }}
                  />

                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wider text-text-subtle">Маршрут</p>
                    {routeData.steps.map((step, i) => (
                      <div key={i} className="flex items-start gap-3 p-2 rounded-lg hover:bg-surface-hover transition-colors">
                        <div className="w-6 h-6 rounded-full bg-accent-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <span className="text-[10px] font-bold text-accent-primary">{i + 1}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-text-primary">{step.text}</p>
                          {step.distance > 0 && (
                            <p className="text-[11px] text-text-muted">{step.distance} м</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  <button
                    onClick={() => { setRouteData(null); setRouteMapLoaded(false); }}
                    className="text-xs text-text-muted hover:text-text-primary transition-colors"
                  >
                    Скрыть маршрут
                  </button>
                </div>
              )}

              {!routeData && !routeLoading && !routeError && (
                <p className="text-sm text-text-muted">
                  Построим оптимальный маршрут от вашего места проживания ({user.location}) до места работы
                </p>
              )}
            </Card>
          )}

          {user?.role === 'student' && job.has_location && !user.location && (
            <Card className="mb-6">
              <div className="flex items-center gap-3 p-4 rounded-xl bg-surface-hover border border-border-default">
                <MapPin size={18} className="text-accent-primary flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-text-primary">Укажите место проживания</p>
                  <p className="text-xs text-text-muted mt-0.5">
                    Чтобы построить маршрут до работы,{' '}
                    <a href="/settings" className="text-accent-primary hover:underline">заполните место проживания</a>{' '}
                    в настройках профиля
                  </p>
                </div>
              </div>
            </Card>
          )}

          <Card>
            <h2 className="font-heading font-semibold text-lg mb-4 flex items-center gap-2">
              <CheckCircle size={18} className="text-accent-primary" />
              Требования
            </h2>
            <ul className="text-sm text-soft/80 leading-relaxed space-y-2">
              <li className="flex items-start gap-2">
                <CheckCircle size={14} className="text-accent mt-0.5 flex-shrink-0" />
                Минимальный возраст: {job.min_age} лет
              </li>
              {!job.experience_required && (
                <li className="flex items-start gap-2">
                  <CheckCircle size={14} className="text-accent mt-0.5 flex-shrink-0" />
                  Опыт работы не требуется
                </li>
              )}
              <li className="flex items-start gap-2">
                <CheckCircle size={14} className="text-accent mt-0.5 flex-shrink-0" />
                Формат: {formatWorkFormat(job.work_format)}
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle size={14} className="text-accent mt-0.5 flex-shrink-0" />
                График: {formatSchedule(job.schedule)}
              </li>
            </ul>
          </Card>
        </div>

        <div>
          <Card className="sticky top-24 space-y-6">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-btn bg-gradient-to-br from-accent/20 to-accent-cyan/20 flex items-center justify-center border border-white/[0.08]">
                  <Building2 size={20} className="text-accent" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{job.employer?.company_name || 'Компания'}</h3>
                  {job.employer?.is_verified && (
                    <span className="text-xs text-success flex items-center gap-1">
                      <CheckCircle size={10} /> Верифицирована
                    </span>
                  )}
                  {job.employer?.description && (
                    <p className="text-xs text-muted mt-1">{job.employer.description}</p>
                  )}
                </div>
              </div>

              {job.employer?.website && (
                <a
                  href={job.employer.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-accent hover:text-accent-cyan mb-2"
                >
                  <Globe size={12} />
                  {job.employer.website}
                </a>
              )}

              {job.employer?.address && (
                <div className="flex items-center gap-1.5 text-xs text-muted mb-4">
                  <MapPin size={12} />
                  {job.employer.address}
                </div>
              )}

              <div className="pt-4 border-t border-white/[0.06] space-y-2">
                <p className="text-xs text-muted">
                  Опубликовано: {formatDate(job.created_at)}
                </p>

                {job.applications_count > 0 && (
                  <p className="text-xs text-muted">
                    Откликов: {job.applications_count}
                  </p>
                )}

                {job.source === 'somon_tj' && job.source_url && (
                  <a
                    href={job.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-xs text-accent hover:text-accent-cyan"
                  >
                    <Globe size={12} />
                    Источник: somon.tj
                  </a>
                )}
              </div>
            </div>

            <div className="pt-4 border-t border-white/[0.06] space-y-3">
              {user?.role === 'student' && (
                applied ? (
                  <div className="bg-success/12 text-success text-sm text-center py-3 rounded-btn">
                    Вы уже откликнулись
                  </div>
                ) : (
                  <Button onClick={() => setApplyOpen(true)} className="w-full">
                    <Send size={16} className="mr-2" />
                    Откликнуться
                  </Button>
                )
              )}

              {user?.role === 'student' && job.employer?.user?.id && (
                <Link href={`/chat?user=${job.employer.user.id}`}>
                  <Button variant="secondary" className="w-full">
                    <MessageSquare size={16} className="mr-2" />
                    Написать работодателю
                  </Button>
                </Link>
              )}

              {!user && (
                <Link href="/auth/login">
                  <Button className="w-full" variant="secondary">Войти, чтобы откликнуться</Button>
                </Link>
              )}
            </div>
          </Card>
        </div>
      </div>

      <Modal open={applyOpen} onClose={() => setApplyOpen(false)} title="Отклик на вакансию">
        {resumes.length === 0 ? (
          <div className="text-center py-4">
            <p className="text-sm text-muted mb-4">У вас нет резюме. Создайте резюме, чтобы откликнуться.</p>
            <Link href="/profile/student">
              <Button variant="secondary">Создать резюме</Button>
            </Link>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <Select
              label="Выберите резюме"
              value={selectedResume}
              onChange={(value) => setSelectedResume(value)}
              options={resumes.map((r) => ({ value: String(r.id), label: r.title }))}
              placeholder="Резюме..."
            />
            {selectedResume && (() => {
              const resume = resumes.find((r) => r.id === Number(selectedResume));
              if (resume?.style) {
                return (
                  <div className="relative">
                    <ResumeStyleSelector
                      value={resume.style}
                      label="Стиль резюме"
                    />
                  </div>
                );
              }
              return null;
            })()}
            <Textarea
              label="Сопроводительное письмо (необязательно)"
              placeholder="Расскажите о себе и почему хотите работать здесь..."
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
            />
            <Button onClick={handleApply} loading={applying} disabled={!selectedResume}>
              Отправить отклик
            </Button>
          </div>
        )}
      </Modal>
    </div>
  );
}
