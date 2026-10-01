import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// /api/auth/refresh must be reachable without an access token: the refresh
// token travels in the request body precisely because the access token has
// expired. Without it listed here the middleware rejected it with 401, so the
// refresh could never run and every session died after one hour.
const publicPaths = [
  '/login', '/forgot-password', '/reset-password', '/health',
  '/api/auth/login', '/api/auth/refresh',
  '/api/auth/forgot-password', '/api/auth/verify-otp', '/api/auth/reset-password',
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (publicPaths.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const token = request.cookies.get('access_token')?.value;
  if (!token && !pathname.startsWith('/api/')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  if (pathname.startsWith('/api/')) {
    const authHeader = request.headers.get('authorization');
    const cookieToken = request.cookies.get('access_token')?.value;
    if (!authHeader?.startsWith('Bearer ') && !cookieToken && !publicPaths.some((p) => pathname.startsWith(p))) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
