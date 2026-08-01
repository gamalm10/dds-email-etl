import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const publicPaths = ['/login', '/register', '/forgot-password', '/reset-password', '/api/auth/login', '/api/auth/register', '/api/auth/forgot-password', '/api/auth/verify-otp', '/api/auth/reset-password', '/health'];

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
