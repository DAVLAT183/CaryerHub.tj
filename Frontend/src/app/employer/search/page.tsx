'use client';

import { useState, useEffect } from 'react';
import { Search, Users, Filter, MapPin, Briefcase } from 'lucide-react';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import Skeleton from '@/components/ui/Skeleton';
import Breadcrumbs from '@/components/ui/Breadcrumbs';
import { showToast, getErrorMessage } from '@/lib/utils';

interface Student {
  id: number;
  username: string;
  email: string;
  location: string;
  student_profile?: {
    university: string;
    faculty: string;
    course: number;
  };
  resumes?: { title: string; skills: string[] }[];
}

export default function EmployerSearchPage() {
  const { user } = useAuth();
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (user?.role !== 'employer') return;
    setLoading(true);
    api.get('/users/?role=student')
      .then((res) => {
        const data = res.data;
        setStudents(data.results || data);
      })
      .catch((err) => showToast(getErrorMessage(err), 'error'))
      .finally(() => setLoading(false));
  }, [user]);

  if (user?.role !== 'employer') {
    return (
      <div className="max-w-[1280px] mx-auto px-6 py-16 text-center">
        <Users size={48} className="text-text-muted mx-auto mb-4" />
        <h1 className="font-heading font-bold text-2xl mb-2">Поиск кандидатов</h1>
        <p className="text-text-muted">Эта функция доступна только для работодателей</p>
      </div>
    );
  }

  const filtered = students.filter((s) => {
    const q = search.toLowerCase();
    return s.username.toLowerCase().includes(q) ||
      s.location?.toLowerCase().includes(q) ||
      s.student_profile?.university?.toLowerCase().includes(q);
  });

  return (
    <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-8 sm:py-12">
      <Breadcrumbs
        items={[
          { label: 'Профиль', href: '/profile/employer' },
          { label: 'Поиск кандидатов' },
        ]}
        className="mb-3"
      />
      <div className="mb-8">
        <h1 className="font-heading font-bold text-3xl md:text-4xl mb-3">Поиск кандидатов</h1>
        <p className="text-text-muted text-lg">Найдите лучших студентов для вашей команды</p>
      </div>

      <div className="flex gap-3 mb-8">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск по имени, городу, университету..."
            className="w-full pl-10 pr-4 py-3 rounded-xl bg-surface-card border border-border-default text-sm text-text-primary placeholder:text-text-subtle focus:outline-none focus:border-accent-primary"
          />
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-card" />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16">
          <Users size={48} className="text-text-muted mx-auto mb-4" />
          <p className="text-text-muted">Кандидаты не найдены</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((student) => (
            <div key={student.id} className="card-minimal p-5 hover:border-accent-primary/30 transition-colors">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-accent-primary/20 flex items-center justify-center">
                  <span className="text-sm font-bold text-accent-primary">{student.username[0].toUpperCase()}</span>
                </div>
                <div>
                  <h3 className="font-medium text-sm">{student.username}</h3>
                  {student.location && (
                    <p className="text-xs text-text-muted flex items-center gap-1">
                      <MapPin size={10} />
                      {student.location}
                    </p>
                  )}
                </div>
              </div>
              {student.student_profile && (
                <div className="space-y-1 text-xs text-text-muted">
                  {student.student_profile.university && (
                    <p className="flex items-center gap-1.5">
                      <Briefcase size={10} />
                      {student.student_profile.university}
                    </p>
                  )}
                  {student.student_profile.course && (
                    <p>{student.student_profile.course} курс</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
