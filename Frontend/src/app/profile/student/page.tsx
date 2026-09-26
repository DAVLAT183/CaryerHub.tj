'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { User, MapPin, GraduationCap, BookOpen, Calendar, Plus, Pencil, Trash2, Sparkles, Zap, Download, FileText, ChevronRight, CheckCircle, Camera, Loader2 } from 'lucide-react';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useI18n } from '@/i18n/I18nContext';
import Input from '@/components/ui/Input';
import Textarea from '@/components/ui/Textarea';
import Select from '@/components/ui/Select';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import Modal from '@/components/ui/Modal';
import Skeleton from '@/components/ui/Skeleton';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import Avatar from '@/components/ui/Avatar';
import ResumeStyleSelector, { STYLE_OPTIONS } from '@/components/ui/ResumeStyleSelector';
import ResumeGeneratorModal from '@/components/chat/ResumeGeneratorModal';
import { formatSchedule, formatWorkFormat, formatResumeStyle, formatDate, showToast, getErrorMessage } from '@/lib/utils';
import type { StudentProfile, Resume, ResumeStyle } from '@/types';

const STYLE_OPTIONS_MAP = Object.fromEntries(
  STYLE_OPTIONS.map((o: (typeof STYLE_OPTIONS)[number]) => [o.value, o])
);

interface AIResume {
  title: string;
  about: string;
  skills: string[];
  schedule_type: string;
  work_format: string;
}

export default function StudentProfilePage() {
  const { user, updateUser } = useAuth();
  const { t } = useI18n();
  const router = useRouter();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [resumeModalOpen, setResumeModalOpen] = useState(false);
  const [editingResume, setEditingResume] = useState<Resume | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResume, setAiResume] = useState<AIResume | null>(null);
  const [aiPreviewOpen, setAiPreviewOpen] = useState(false);
  const [resumeGenOpen, setResumeGenOpen] = useState(false);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement>(null);

  const uploadAvatar = async (file: File) => {
    setAvatarUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post('/users/me/avatar/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      updateUser(res.data);
      showToast(t('profile.photoUpdated'), 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setAvatarUploading(false);
    }
  };

  const removeAvatar = async () => {
    setAvatarUploading(true);
    try {
      const res = await api.delete('/users/me/avatar/');
      updateUser(res.data);
      showToast(t('profile.photoRemoved'), 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setAvatarUploading(false);
    }
  };

  const [profileForm, setProfileForm] = useState({
    university: '',
    faculty: '',
    course: '',
    city: '',
  });

  const [locationForm, setLocationForm] = useState('');

  const [resumeForm, setResumeForm] = useState({
    title: '',
    about: '',
    skills: '',
    schedule_type: 'flexible',
    work_format: 'online',
    style: 'modern' as ResumeStyle,
    github_url: '',
    portfolio_url: '',
    linkedin_url: '',
  });

  useEffect(() => {
    if (!user) return;
    Promise.all([
      api.get('/student-profiles/').then((r) => {
        const data = r.data;
        const list = data.results || data;
        return list[0] as StudentProfile;
      }),
      api.get('/resumes/').then((r) => {
        const data = r.data;
        return (data.results || data) as Resume[];
      }),
    ]).then(([p, r]) => {
      setProfile(p);
      setResumes(r);
      setLocationForm(user?.location || '');
      if (p) {
        setProfileForm({
          university: p.university || '',
          faculty: p.faculty || '',
          course: p.course?.toString() || '',
          city: p.city || '',
        });
      }
    }).catch((err) => {
      showToast(getErrorMessage(err), 'error');
    }).finally(() => setLoading(false));
  }, [user]);

  const saveProfile = async () => {
    if (!profile) return;
    try {
      await api.patch('/users/me/', { location: locationForm });
      await api.patch(`/student-profiles/${profile.id}/`, {
        ...profileForm,
        course: profileForm.course ? Number(profileForm.course) : null,
      });
      setEditing(false);
      const res = await api.get(`/student-profiles/${profile.id}/`);
      setProfile(res.data);
      showToast(t('profile.profileSaved'), 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const saveResume = async () => {
    try {
      const payload = {
        ...resumeForm,
        skills: resumeForm.skills.split(',').map((s) => s.trim()).filter(Boolean),
        github_url: resumeForm.github_url || null,
        portfolio_url: resumeForm.portfolio_url || null,
        linkedin_url: resumeForm.linkedin_url || null,
      };
      const isEditing = !!editingResume;
      if (editingResume) {
        await api.patch(`/resumes/${editingResume.id}/`, payload);
      } else {
        await api.post('/resumes/', payload);
      }
      const res = await api.get('/resumes/');
      const data = res.data;
      setResumes(data.results || data);
      setResumeModalOpen(false);
      setEditingResume(null);
      setResumeForm({ title: '', about: '', skills: '', schedule_type: 'flexible', work_format: 'online', style: 'modern', github_url: '', portfolio_url: '', linkedin_url: '' });
      showToast(isEditing ? t('notifications.resumeUpdated') : t('notifications.resumeCreated'), 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const deleteResume = async (id: number) => {
    if (!confirm(t('profile.confirmDeleteResume'))) return;
    try {
      await api.delete(`/resumes/${id}/`);
      setResumes((prev) => prev.filter((r) => r.id !== id));
      showToast(t('profile.resumeDeleted'), 'info');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  const generateAIResume = async () => {
    setAiLoading(true);
    try {
      const res = await api.post<AIResume>('/ai/generate-resume/');
      setAiResume(res.data);
      setAiPreviewOpen(true);
      showToast(t('profile.resumeGenerated'), 'success');
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    } finally {
      setAiLoading(false);
    }
  };

  const saveAIResume = () => {
    useAIResume();
  };

  const useAIResume = () => {
    if (!aiResume) return;
    setResumeForm({
      title: aiResume.title,
      about: aiResume.about,
      skills: aiResume.skills.join(', '),
      schedule_type: aiResume.schedule_type,
      work_format: aiResume.work_format,
      style: 'modern',
      github_url: '',
      portfolio_url: '',
      linkedin_url: '',
    });
    setEditingResume(null);
    setAiPreviewOpen(false);
    setResumeModalOpen(true);
  };

  const downloadResumePDF = async (resumeId: number, style?: ResumeStyle) => {
    try {
      const params: Record<string, string> = {};
      if (style) params.style = style;
      const res = await api.get(`/resumes/${resumeId}/pdf/`, { params, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      const styleKey = style || 'modern';
      link.setAttribute('download', `resume_${resumeId}_${t(`resumeStyles.${styleKey}`)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      showToast(getErrorMessage(err), 'error');
    }
  };

  if (loading) {
    return (
      <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
        <Skeleton className="h-8 w-48 mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <Skeleton className="h-64 rounded-card" />
          <div className="lg:col-span-2">
            <Skeleton className="h-40 rounded-card mb-4" />
            <Skeleton className="h-40 rounded-card" />
          </div>
        </div>
      </div>
    );
  }

  const profileSteps = [
    { key: 'location', label: t('profile.location'), value: user?.location, icon: MapPin },
    { key: 'university', label: t('profile.university'), value: profile?.university, icon: GraduationCap },
    { key: 'faculty', label: t('profile.faculty'), value: profile?.faculty, icon: BookOpen },
    { key: 'course', label: t('profile.course'), value: profile?.course?.toString(), icon: Calendar },
    { key: 'city', label: t('profile.city'), value: profile?.city, icon: MapPin },
  ];

  const completedSteps = profileSteps.filter((s) => !!s.value).length;
  const totalSteps = profileSteps.length;
  const profileComplete = completedSteps === totalSteps;

  return (
    <div className="max-w-[1200px] mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <Breadcrumbs
        items={[{ label: t('profile.title'), href: '/profile' }, { label: t('auth.roleStudent') }]}
        className="mb-3"
      />
      <h1 className="font-heading font-bold text-xl sm:text-[28px] text-text-primary tracking-tight mb-6 sm:mb-8">{t('profile.myProfile')}</h1>

      {/* Profile Completion Prompt */}
      {!profileComplete && (
        <div className="mb-6 p-5 rounded-2xl bg-gradient-to-r from-accent-primary/5 via-accent-cyan/5 to-accent-primary/5 border border-accent-primary/20">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-2xl bg-accent-primary/10 flex items-center justify-center flex-shrink-0">
              <FileText size={22} className="text-accent-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-heading font-semibold text-[15px] text-text-primary mb-1">{t('profile.fillProfile')}</h3>
              <p className="text-[13px] text-text-muted mb-4">
                {t('profile.fillProfileProgress', { completed: completedSteps, total: totalSteps })}
              </p>
              <div className="flex flex-col gap-2.5">
                {profileSteps.map((step) => (
                  <div key={step.key} className="flex items-center gap-3">
                    {step.value ? (
                      <CheckCircle size={16} className="text-accent-primary flex-shrink-0" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border-2 border-border-default flex-shrink-0" />
                    )}
                    <span className={`text-[13px] ${step.value ? 'text-text-primary' : 'text-text-muted'}`}>
                      {step.label}
                    </span>
                    {step.value && (
                      <span className="text-[12px] text-accent-primary font-medium ml-auto truncate max-w-[200px]">{step.value}</span>
                    )}
                    {!step.value && (
                      <button
                        onClick={() => setEditing(true)}
                        className="text-[12px] text-accent-primary font-medium ml-auto hover:underline"
                      >
                        {t('profile.fill')}
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center gap-3">
                <div className="flex-1 h-2 rounded-full bg-surface-hover overflow-hidden">
                  <div
                    className="h-full rounded-full bg-accent-primary transition-all duration-500"
                    style={{ width: `${(completedSteps / totalSteps) * 100}%` }}
                  />
                </div>
                <span className="text-[12px] font-semibold text-accent-primary">{Math.round((completedSteps / totalSteps) * 100)}%</span>
              </div>
              <button
                onClick={() => setEditing(true)}
                className="mt-4 flex items-center gap-2 px-4 py-2 rounded-xl bg-accent-primary text-white text-[13px] font-semibold hover:bg-accent-primary-hover transition-colors"
              >
                {t('profile.fillProfileBtn')}
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sidebar */}
        <div>
          <div className="card-minimal p-6">
            <div className="text-center mb-6">
              <div className="mx-auto mb-3 w-[72px] h-[72px] relative group">
                <Avatar src={user?.avatar} alt={user?.username} size="xl" />
                <button
                  type="button"
                  onClick={() => avatarInputRef.current?.click()}
                  disabled={avatarUploading}
                  title={t('profile.changePhoto')}
                  className="absolute inset-0 rounded-2xl bg-black/50 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity disabled:opacity-100"
                >
                  {avatarUploading ? <Loader2 size={22} className="animate-spin" /> : <Camera size={22} />}
                </button>
                <input
                  ref={avatarInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  className="hidden"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    e.target.value = '';
                    if (file) uploadAvatar(file);
                  }}
                />
              </div>
              <h2 className="font-heading font-semibold text-[17px] text-text-primary">{user?.username}</h2>
              <p className="text-[13px] text-text-muted mt-0.5">{user?.email}</p>
              <div className="flex items-center justify-center gap-2 mt-2">
                <button
                  type="button"
                  onClick={() => avatarInputRef.current?.click()}
                  disabled={avatarUploading}
                  className="text-[12px] font-medium text-accent-primary hover:underline disabled:opacity-50"
                >
                  {t('profile.changePhoto')}
                </button>
                {user?.avatar && (
                  <>
                    <span className="text-text-subtle text-[12px]">·</span>
                    <button
                      type="button"
                      onClick={removeAvatar}
                      disabled={avatarUploading}
                      className="text-[12px] font-medium text-text-muted hover:text-error transition-colors disabled:opacity-50"
                    >
                      {t('profile.removePhoto')}
                    </button>
                  </>
                )}
              </div>
            </div>

            <div className="space-y-3.5">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-surface-hover flex items-center justify-center flex-shrink-0">
                  <GraduationCap size={16} className="text-text-muted" />
                </div>
                <span className="text-[13px] text-text-secondary truncate">{profile?.university || t('profile.universityNotSpecified')}</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-surface-hover flex items-center justify-center flex-shrink-0">
                  <BookOpen size={16} className="text-text-muted" />
                </div>
                <span className="text-[13px] text-text-secondary truncate">{profile?.faculty || t('profile.facultyNotSpecified')}</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-surface-hover flex items-center justify-center flex-shrink-0">
                  <Calendar size={16} className="text-text-muted" />
                </div>
                <span className="text-[13px] text-text-secondary">{profile?.course ? t('profile.courseN', { n: profile.course }) : t('profile.courseNotSpecified')}</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-surface-hover flex items-center justify-center flex-shrink-0">
                  <MapPin size={16} className="text-text-muted" />
                </div>
                <span className="text-[13px] text-text-secondary">{user?.location || profile?.city || t('profile.cityNotSpecified')}</span>
              </div>
            </div>

            <div className="mt-6 pt-5 border-t border-border-default">
              <button
                onClick={() => router.push('/recommendations')}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-[13px] font-medium text-accent-primary bg-accent-primary/10 hover:bg-accent-primary/15 transition-colors"
              >
                <Sparkles size={14} />
                {t('nav.recommendations')}
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Personal Data */}
          <div className="card-minimal p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4 sm:mb-5">
              <h3 className="font-heading font-semibold text-[14px] sm:text-[16px] text-text-primary">{t('profile.personalData')}</h3>
              <button
                onClick={() => setEditing(!editing)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[13px] font-medium text-text-muted hover:text-text-primary hover:bg-surface-hover transition-colors"
              >
                <Pencil size={13} />
                {editing ? t('common.cancel') : t('common.edit')}
              </button>
            </div>

            {editing ? (
              <div className="flex flex-col gap-4">
                <Input
                  label={t('profile.location')}
                  value={locationForm}
                  onChange={(e) => setLocationForm(e.target.value)}
                  placeholder="Душанбе, Таджикистан"
                />
                <Input
                  label={t('profile.university')}
                  value={profileForm.university}
                  onChange={(e) => setProfileForm((f) => ({ ...f, university: e.target.value }))}
                />
                <Input
                  label={t('profile.faculty')}
                  value={profileForm.faculty}
                  onChange={(e) => setProfileForm((f) => ({ ...f, faculty: e.target.value }))}
                />
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label={t('profile.course')}
                    type="number"
                    value={profileForm.course}
                    onChange={(e) => setProfileForm((f) => ({ ...f, course: e.target.value }))}
                  />
                  <Input
                    label={t('profile.city')}
                    value={profileForm.city}
                    onChange={(e) => setProfileForm((f) => ({ ...f, city: e.target.value }))}
                  />
                </div>
                <button
                  onClick={saveProfile}
                  className="w-full py-2.5 rounded-xl bg-accent-primary text-white text-[14px] font-semibold hover:bg-accent-primary-hover transition-colors"
                >
                  {t('common.save')}
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div className="p-4 rounded-xl bg-surface-hover border border-border-default">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-text-subtle">{t('profile.location')}</span>
                  <p className={`text-[14px] mt-1 font-medium ${user?.location ? 'text-text-primary' : 'text-text-subtle'}`}>
                    {user?.location || '—'}
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-surface-hover border border-border-default">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-text-subtle">{t('profile.university')}</span>
                  <p className={`text-[14px] mt-1 font-medium ${profile?.university ? 'text-text-primary' : 'text-text-subtle'}`}>
                    {profile?.university || '—'}
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-surface-hover border border-border-default">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-text-subtle">{t('profile.faculty')}</span>
                  <p className={`text-[14px] mt-1 font-medium ${profile?.faculty ? 'text-text-primary' : 'text-text-subtle'}`}>
                    {profile?.faculty || '—'}
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-surface-hover border border-border-default">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-text-subtle">{t('profile.course')}</span>
                  <p className={`text-[14px] mt-1 font-medium ${profile?.course ? 'text-text-primary' : 'text-text-subtle'}`}>
                    {profile?.course || '—'}
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-surface-hover border border-border-default">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-text-subtle">{t('profile.city')}</span>
                  <p className={`text-[14px] mt-1 font-medium ${profile?.city ? 'text-text-primary' : 'text-text-subtle'}`}>
                    {profile?.city || '—'}
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Resumes */}
          <div className="card-minimal p-4 sm:p-6">
            <div className="flex items-center justify-between mb-4 sm:mb-5">
              <h3 className="font-heading font-semibold text-[14px] sm:text-[16px] text-text-primary">{t('profile.resumesCount', { n: resumes.length })}</h3>
              <div className="flex gap-1.5 sm:gap-2">
                <button
                  onClick={() => setResumeGenOpen(true)}
                  className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg sm:rounded-xl text-[11px] sm:text-[13px] font-medium border border-accent-primary/30 bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/15 transition-colors"
                >
                  <Sparkles size={11} className="sm:hidden" />
                  <Sparkles size={13} className="hidden sm:block" />
                  {t('profile.aiChat')}
                </button>
                <button
                  onClick={() => { setEditingResume(null); setResumeModalOpen(true); }}
                  className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg sm:rounded-xl text-[11px] sm:text-[13px] font-medium bg-accent-primary text-white hover:bg-accent-primary-hover transition-colors"
                >
                  <Plus size={11} className="sm:hidden" />
                  <Plus size={13} className="hidden sm:block" />
                  {t('common.create')}
                </button>
              </div>
            </div>

            {resumes.length === 0 ? (
              <div className="text-center py-12 rounded-xl bg-gradient-to-br from-accent-primary/5 to-accent-cyan/5 border border-dashed border-accent-primary/30">
                <div className="w-16 h-16 rounded-2xl bg-accent-primary/10 flex items-center justify-center mx-auto mb-4">
                  <FileText size={28} className="text-accent-primary" />
                </div>
                <h4 className="font-heading font-semibold text-lg text-text-primary mb-2">{t('profile.createFirstResume')}</h4>
                <p className="text-[13px] text-text-muted mb-6 max-w-sm mx-auto">
                  {t('profile.createFirstResumeDesc')}
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                  <button
                    onClick={() => setResumeGenOpen(true)}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-[13px] font-semibold border border-accent-primary/30 bg-accent-primary/10 text-accent-primary hover:bg-accent-primary/15 transition-colors"
                  >
                    <Sparkles size={15} />
                    {t('profile.createWithAI')}
                  </button>
                  <button
                    onClick={() => { setEditingResume(null); setResumeModalOpen(true); }}
                    className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-[13px] font-semibold bg-accent-primary text-white hover:bg-accent-primary-hover transition-colors"
                  >
                    <Plus size={15} />
                    {t('profile.createManually')}
                  </button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {resumes.map((resume) => (
                  <div key={resume.id} className="flex items-center justify-between p-4 rounded-xl bg-surface-hover border border-border-default hover:border-border-hover transition-colors">
                    <div className="flex-1 min-w-0">
                      <h4 className="text-[14px] font-medium text-text-primary">{resume.title}</h4>
                      <p className="text-[12px] text-text-muted mt-0.5">{t('resume.updated')} {formatDate(resume.updated_at)}</p>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {resume.style && (
                          <span className="inline-flex items-center gap-1.5 text-[11px] font-medium px-2 py-0.5 rounded-lg bg-surface-card border border-border-default text-text-muted">
                            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: STYLE_OPTIONS_MAP[resume.style]?.color || '#6B7078' }} />
                            {formatResumeStyle(resume.style)}
                          </span>
                        )}
                        <span className="text-[11px] font-medium px-2 py-0.5 rounded-lg bg-surface-card border border-border-default text-text-muted">
                          {formatSchedule(resume.schedule_type)}
                        </span>
                        <span className="text-[11px] font-medium px-2 py-0.5 rounded-lg bg-surface-card border border-border-default text-text-muted">
                           {formatWorkFormat(resume.work_format)}
                         </span>
                         {resume.github_url && (
                           <a href={resume.github_url} target="_blank" rel="noopener noreferrer" className="text-[11px] font-medium px-2 py-0.5 rounded-lg bg-surface-card border border-border-default text-accent-primary hover:text-accent-primary-hover transition-colors">
                             GitHub
                           </a>
                         )}
                          {resume.portfolio_url && (
                            <a href={resume.portfolio_url} target="_blank" rel="noopener noreferrer" className="text-[11px] font-medium px-2 py-0.5 rounded-lg bg-surface-card border border-border-default text-accent-primary hover:text-accent-primary-hover transition-colors">
                              {t('profile.portfolio')}
                           </a>
                         )}
                         {resume.linkedin_url && (
                           <a href={resume.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-[11px] font-medium px-2 py-0.5 rounded-lg bg-surface-card border border-border-default text-accent-primary hover:text-accent-primary-hover transition-colors">
                             LinkedIn
                           </a>
                         )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => downloadResumePDF(resume.id, resume.style)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold text-white bg-accent-primary hover:bg-accent-primary-hover transition-colors"
                        title={t('profile.downloadPDF')}
                      >
                        <Download size={13} />
                        PDF
                      </button>
                      <button
                        onClick={() => {
                          setEditingResume(resume);
                          setResumeForm({
                            title: resume.title,
                            about: resume.about,
                            skills: resume.skills.join(', '),
                            schedule_type: resume.schedule_type,
                            work_format: resume.work_format,
                            style: resume.style || 'modern',
                            github_url: resume.github_url || '',
                            portfolio_url: resume.portfolio_url || '',
                            linkedin_url: resume.linkedin_url || '',
                          });
                          setResumeModalOpen(true);
                        }}
                        className="p-2 text-text-muted hover:text-text-primary hover:bg-surface-active rounded-lg transition-colors"
                        title={t('common.edit')}
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        onClick={() => deleteResume(resume.id)}
                        className="p-2 text-text-muted hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                        title={t('common.delete')}
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI Resume Preview Modal */}
      <Modal
        open={aiPreviewOpen}
        onClose={() => { setAiPreviewOpen(false); setAiResume(null); }}
        title={t('profile.aiResumeTitle')}
      >
        {aiResume && (
          <div className="flex flex-col gap-4">
            <div className="p-5 rounded-[var(--radius-lg)] bg-[var(--color-bg-secondary)] border border-[var(--color-border-default)]">
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-8 h-8 rounded-full bg-[var(--color-accent-primary)]/15 flex items-center justify-center">
                  <Sparkles size={14} className="text-[var(--color-accent-primary)]" />
                </div>
                <h4 className="text-sm font-semibold text-[var(--color-text-primary)]">{aiResume.title}</h4>
              </div>
              <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed mb-3">{aiResume.about}</p>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {aiResume.skills.map((skill, i) => (
                  <Badge key={i} variant="default">{skill}</Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <Badge variant={aiResume.schedule_type === 'flexible' ? 'flexible' : 'default'}>
                  {formatSchedule(aiResume.schedule_type)}
                </Badge>
                <Badge variant={aiResume.work_format === 'online' ? 'online' : 'default'}>
                  {formatWorkFormat(aiResume.work_format)}
                </Badge>
              </div>
            </div>

            <div className="flex gap-3">
              <Button onClick={saveAIResume} className="flex-1">
                <Sparkles size={14} className="mr-1" />
                {t('profile.editAndSave')}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Manual Resume Modal */}
      <Modal
        open={resumeModalOpen}
        onClose={() => { setResumeModalOpen(false); setEditingResume(null); }}
        title={editingResume ? t('profile.editResume') : t('profile.newResume')}
      >
        <div className="flex flex-col gap-4">
          <Input
            label={t('resume.desiredPosition')}
            value={resumeForm.title}
            onChange={(e) => setResumeForm((f) => ({ ...f, title: e.target.value }))}
            placeholder="Frontend Developer"
          />
          <Textarea
            label={t('resume.about')}
            value={resumeForm.about}
            onChange={(e) => setResumeForm((f) => ({ ...f, about: e.target.value }))}
            placeholder={t('resume.aboutPlaceholder')}
          />
          <Input
            label={t('resume.skillsComma')}
            value={resumeForm.skills}
            onChange={(e) => setResumeForm((f) => ({ ...f, skills: e.target.value }))}
            placeholder="JavaScript, React, TypeScript"
          />
          <div className="grid grid-cols-2 gap-4">
            <Select
              label={t('employer.schedule')}
              value={resumeForm.schedule_type}
              onChange={(value) => setResumeForm((f) => ({ ...f, schedule_type: value }))}
              options={[
                { value: 'flexible', label: t('schedule.flexible') },
                { value: 'part_time', label: t('schedule.part_time') },
                { value: 'full_time', label: t('schedule.full_time') },
              ]}
            />
            <Select
              label={t('employer.workFormat')}
              value={resumeForm.work_format}
              onChange={(value) => setResumeForm((f) => ({ ...f, work_format: value }))}
              options={[
                { value: 'online', label: t('workFormat.online') },
                { value: 'offline', label: t('workFormat.offline') },
                { value: 'hybrid', label: t('workFormat.hybrid') },
              ]}
            />
          </div>
          <div className="relative">
            <ResumeStyleSelector
              label={t('resume.styleLabel')}
              value={resumeForm.style}
              onChange={(style) => setResumeForm((f) => ({ ...f, style }))}
            />
          </div>
          <div className="border-t border-border-default pt-4 mt-2">
            <p className="text-[12px] text-text-muted mb-3">{t('resume.optionalLinks')}</p>
            <div className="flex flex-col gap-3">
              <Input
                label="GitHub"
                value={resumeForm.github_url}
                onChange={(e) => setResumeForm((f) => ({ ...f, github_url: e.target.value }))}
                placeholder="https://github.com/username"
              />
              <Input
                label={t('profile.portfolio')}
                value={resumeForm.portfolio_url}
                onChange={(e) => setResumeForm((f) => ({ ...f, portfolio_url: e.target.value }))}
                placeholder="https://mysite.com"
              />
              <Input
                label="LinkedIn"
                value={resumeForm.linkedin_url}
                onChange={(e) => setResumeForm((f) => ({ ...f, linkedin_url: e.target.value }))}
                placeholder="https://linkedin.com/in/username"
              />
            </div>
          </div>
          <Button onClick={saveResume}>
            {editingResume ? t('common.save') : t('common.create')}
          </Button>
        </div>
      </Modal>
      {/* Resume Generator Chat Modal */}
      <ResumeGeneratorModal
        open={resumeGenOpen}
        onClose={() => setResumeGenOpen(false)}
        onCreated={() => {
          api.get('/resumes/').then((r) => {
            const data = r.data;
            setResumes(data.results || data);
          }).catch(() => {});
        }}
      />
    </div>
  );
}
