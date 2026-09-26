export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'student' | 'employer';
  phone: string;
  avatar: string | null;
  location: string;
  is_email_verified?: boolean;
}

export interface StudentProfile {
  id: number;
  user: User;
  university: string;
  faculty: string;
  course: number | null;
  birth_date: string | null;
  age: number | null;
  city: string;
}

export interface EmployerProfile {
  id: number;
  user: User | null;
  company_name: string;
  description: string;
  website: string;
  address: string;
  is_verified: boolean;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  jobs_count?: number;
}

export type ResumeStyle = 'classic' | 'modern' | 'minimal' | 'creative';

export interface Resume {
  id: number;
  student: StudentProfile;
  title: string;
  about: string;
  skills: string[];
  schedule_type: 'flexible' | 'part_time' | 'full_time';
  work_format: 'online' | 'offline' | 'hybrid';
  github_url: string | null;
  portfolio_url: string | null;
  linkedin_url: string | null;
  style: ResumeStyle;
  created_at: string;
  updated_at: string;
}

export interface Job {
  id: number;
  employer: EmployerProfile;
  category: number;
  category_name: string;
  title: string;
  description: string;
  salary_min: number | null;
  salary_max: number | null;
  min_age: number;
  schedule: 'flexible' | 'part_time' | 'full_time';
  work_format: 'online' | 'offline' | 'hybrid';
  experience_required: boolean;
  is_active: boolean;
  created_at: string;
  applications_count: number;
  is_favorited: boolean;
  image: string | null;
  image_url: string | null;
  location_lat: number | null;
  location_lng: number | null;
  location_address: string;
  has_location: boolean;
  source: string;
  source_url: string;
  source_id: string;
}

export interface Application {
  id: number;
  job: number | { id: number };
  job_title: string;
  job_employer_name: string;
  resume: number | { id: number };
  student_name: string;
  status: 'sent' | 'viewed' | 'interview' | 'accepted' | 'rejected';
  cover_letter: string;
  created_at: string;
}

export interface Favorite {
  id: number;
  job: Job;
  job_id: number;
  created_at: string;
}

export interface RecommendedJob extends Job {
  match_score: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  role: 'student' | 'employer';
  phone?: string;
}

export interface DirectMessage {
  id: number;
  sender: number;
  sender_name: string;
  recipient: number;
  recipient_name: string;
  content: string;
  created_at: string;
  is_read: boolean;
}

export interface ChatSession {
  id: number;
  title: string;
  last_message: { role: string; content: string } | null;
  messages_count: number;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: number;
  notification_type: 'application_viewed' | 'application_accepted' | 'application_rejected' | 'application_interview' | 'message' | 'system';
  title: string;
  message: string;
  link: string;
  is_read: boolean;
  created_at: string;
  employer_avatar: string | null;
}
