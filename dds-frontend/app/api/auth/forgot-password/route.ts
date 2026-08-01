import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  try {
    const body = await request.json();
    const res = await fetch(`${API_URL}/api/v1/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err: any) {
    return NextResponse.json({ detail: 'Failed to send OTP' }, { status: 500 });
  }
}
