import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

function setCookie(name: string, value: string, days: number) {
  if (typeof window === 'undefined') return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function getCookie(name: string): string | null {
  if (typeof window === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

function removeCookie(name: string) {
  if (typeof window === 'undefined') return;
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
}

export function saveTokens(access: string, refresh: string) {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
  setCookie('access_token', access, 1);
}

export function setEmailVerified(verified: boolean) {
  setCookie('email_verified', verified ? 'true' : 'false', 7);
}

export function removeTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  removeCookie('access_token');
  removeCookie('email_verified');
}

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token') || getCookie('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

let isRefreshing = false;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    const detail = error.response?.data?.detail;
    if (error.response?.status === 403 && detail?.code === 'email_not_verified') {
      setEmailVerified(false);
      if (
        typeof window !== 'undefined' &&
        !window.location.pathname.startsWith('/auth/verify-email')
      ) {
        const from = window.location.pathname + window.location.search;
        window.location.assign(`/auth/verify-email?from=${encodeURIComponent(from)}`);
      }
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        removeTokens();
        return Promise.reject(error);
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          const { access } = res.data;
          saveTokens(access, refreshToken);
          originalRequest.headers.Authorization = `Bearer ${access}`;
          isRefreshing = false;
          return api(originalRequest);
        } catch {
          removeTokens();
          isRefreshing = false;
          if (typeof window !== 'undefined') {
            window.location.href = '/auth/login';
          }
        }
      } else {
        removeTokens();
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default api;
