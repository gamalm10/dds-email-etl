import { NextResponse } from 'next/server';
import bcrypt from 'bcryptjs';
import mysql from 'mysql2/promise';
import { signAccessToken, signRefreshToken } from '@/lib/auth';

export async function POST(request: Request) {
  try {
    const { email, password } = await request.json();

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
       WHERE u.email = ? AND u.is_active = TRUE`,
      [email]
    );
    await conn.end();

    const users = rows as any[];
    if (users.length === 0) {
      return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    }

    const user = users[0];
    const valid = await bcrypt.compare(password, user.password_hash);
    if (!valid) {
      return NextResponse.json({ error: 'Invalid credentials' }, { status: 401 });
    }

    const permissions = typeof user.permissions === 'string' ? JSON.parse(user.permissions) : user.permissions;
    const tokenPayload = { userId: user.id, email: user.email, role: user.role_name, permissions };
    const accessToken = await signAccessToken(tokenPayload);
    const refreshToken = await signRefreshToken(tokenPayload);

    const conn2 = await mysql.createConnection({
      host: process.env.MARIA_HOST || 'localhost',
      port: parseInt(process.env.MARIA_PORT || '3307'),
      user: process.env.MARIA_USER || 'dds',
      password: process.env.MARIA_PASSWORD || 'ddspass',
      database: process.env.MARIA_DATABASE || 'dds',
    });
    await conn2.execute(
      'INSERT INTO sessions (user_id, refresh_token, expires_at) VALUES (?, ?, DATE_ADD(NOW(), INTERVAL 7 DAY))',
      [user.id, refreshToken]
    );
    await conn2.execute('UPDATE users SET last_login = NOW() WHERE id = ?', [user.id]);
    await conn2.end();

    const response = NextResponse.json({
      access_token: accessToken,
      refresh_token: refreshToken,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role_id: user.role_id,
        role_name: user.role_name,
        is_active: Boolean(user.is_active),
        last_login: user.last_login,
        created_at: user.created_at,
      },
    });

    response.cookies.set('access_token', accessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 3600,
      path: '/',
    });

    return response;
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
