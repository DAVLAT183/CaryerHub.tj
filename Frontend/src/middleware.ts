import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const protectedRoutes = ['/favorites', '/applications', '/profile/student', '/profile/employer', '/employer/create-job', '/notifications'];
const verifiedRoutes = [
  ...protectedRoutes,
  '/jobs',
  '/chat',
  '/settings',
  '/recommendations',
  '/game',
];
const authRoutes = ['/auth/login', '/auth/register'];

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;
  const emailVerified = request.cookies.get('email_verified')?.value === 'true';
  const pathname = request.nextUrl.pathname;

  const isProtected = protectedRoutes.some((route) => pathname.startsWith(route));
  const needsVerification = verifiedRoutes.some((route) => pathname.startsWith(route));
  const isAuthPage = authRoutes.some((route) => pathname.startsWith(route));

  if (isProtected && !token) {
    const url = request.nextUrl.clone();
    url.pathname = '/auth/login';
    url.search = '';
    url.searchParams.set('from', pathname);
    return NextResponse.redirect(url);
  }

  if (token && !emailVerified && needsVerification) {
    const url = request.nextUrl.clone();
    url.pathname = '/auth/verify-email';
    url.search = '';
    url.searchParams.set('from', pathname);
    return NextResponse.redirect(url);
  }

  if (isAuthPage && token && emailVerified) {
    const url = request.nextUrl.clone();
    url.pathname = '/jobs';
    url.search = '';
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/favorites/:path*',
    '/applications/:path*',
    '/profile/:path*',
    '/employer/:path*',
    '/notifications/:path*',
    '/jobs/:path*',
    '/chat/:path*',
    '/settings/:path*',
    '/recommendations/:path*',
    '/game/:path*',
    '/auth/:path*',
  ],
};
