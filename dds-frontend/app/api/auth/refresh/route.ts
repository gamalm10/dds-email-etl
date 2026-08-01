import { NextResponse } from 'next/server';
import mysql from 'mysql2/promise';
import { verifyRefreshToken, signAccessToken } from '@/lib/auth';

export async function POST(request: Request) {
  try {
    const { refreshToken } = await request.json();
    if (!refreshToken) {
      return NextResponse.json({ error: 'Refresh token required' }, { status: 400 });
    }

    const payload = await verifyRefreshToken(refreshToken);
    if (!payload) {
      return NextResponse.json({ error: 'Invalid refresh token' }, { status: 401 });
    }

    const conn = await mysql.createConnection({
      host: process.env.MARIA_HOST || 'localhost',
      port: parseInt(process.env.MARIA_PORT || '3307'),
      user: process.env.MARIA_USER || 'dds',
      password: process.env.MARIA_PASSWORD || 'ddspass',
      database: process.env.MARIA_DATABASE || 'dds',
    });

    const [rows] = await conn.execute(
      `SELECT u.*, r.name as role_name, r.permissions 
       FROM users u JOIN roles r ON u.role_id = r.id 
       WHERE u.id = ? AND u.is_active = TRUE`,
      [payload.userId]
    );
    await conn.end();

    const users = rows as any[];
    if (users.length === 0) {
      return NextResponse.json({ error: 'User not found' }, { status: 401 });
    }

    const user = users[0];
    const permissions = typeof user.permissions === 'string' ? JSON.parse(user.permissions) : user.permissions;
    const newAccess = await signAccessToken({
      userId: user.id, email: user.email, role: user.role_name, permissions,
    });

    const response = NextResponse.json({ accessToken: newAccess });
    response.cookies.set('access_token', newAccess, {
      httpOnly: true, secure: false, sameSite: 'lax', maxAge: 3600, path: '/',
    });
    return response;
  } catch {
    return NextResponse.json({ error: 'Refresh failed' }, { status: 500 });
  }
}
