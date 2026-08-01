import { NextRequest, NextResponse } from 'next/server';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path);
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path);
}

export async function PUT(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path);
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path);
}

export async function PATCH(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path);
}

async function proxy(request: NextRequest, path: string[]) {
  const url = `${BACKEND}/api/v1/${path.join('/')}`;
  const search = request.nextUrl.search;
  const headers: Record<string, string> = {
    'Content-Type': request.headers.get('content-type') || 'application/json',
  };
  const auth = request.headers.get('authorization');
  if (auth) {
    headers['Authorization'] = auth;
  } else {
    const cookieToken = request.cookies.get('access_token')?.value;
    if (cookieToken) {
      headers['Authorization'] = `Bearer ${cookieToken}`;
    }
  }

  const body = ['POST', 'PUT', 'PATCH'].includes(request.method)
    ? await request.blob()
    : undefined;

  try {
    const res = await fetch(url + search, { method: request.method, headers, body });
    const data = await res.blob();
    return new NextResponse(data, {
      status: res.status,
      headers: { 'Content-Type': res.headers.get('content-type') || 'application/json' },
    });
  } catch (err: any) {
    return NextResponse.json({ error: 'Proxy error', message: err.message }, { status: 502 });
  }
}
