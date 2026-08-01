import { NextResponse } from 'next/server';
import mysql from 'mysql2/promise';

export async function POST(request: Request) {
  try {
    const { refreshToken } = await request.json();

    if (refreshToken) {
      const conn = await mysql.createConnection({
        host: process.env.MARIA_HOST || 'localhost',
        port: parseInt(process.env.MARIA_PORT || '3307'),
        user: process.env.MARIA_USER || 'dds',
        password: process.env.MARIA_PASSWORD || 'ddspass',
        database: process.env.MARIA_DATABASE || 'dds',
      });
      await conn.execute('DELETE FROM sessions WHERE refresh_token = ?', [refreshToken]);
      await conn.end();
    }

    const response = NextResponse.json({ message: 'Logged out' });
    response.cookies.set('access_token', '', { maxAge: 0, path: '/' });
    return response;
  } catch {
    return NextResponse.json({ error: 'Logout failed' }, { status: 500 });
  }
}
