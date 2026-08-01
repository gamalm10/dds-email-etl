import { NextResponse } from 'next/server';
import bcrypt from 'bcryptjs';
import mysql from 'mysql2/promise';

export async function POST(request: Request) {
  try {
    const { username, email, password } = await request.json();

    if (!username || !email || !password) {
      return NextResponse.json({ error: 'All fields required' }, { status: 400 });
    }

    const conn = await mysql.createConnection({
      host: process.env.MARIA_HOST || 'localhost',
      port: parseInt(process.env.MARIA_PORT || '3307'),
      user: process.env.MARIA_USER || 'dds',
      password: process.env.MARIA_PASSWORD || 'ddspass',
      database: process.env.MARIA_DATABASE || 'dds',
    });

    const [existing] = await conn.execute(
      'SELECT id FROM users WHERE email = ? OR username = ?',
      [email, username]
    );
    if ((existing as any[]).length > 0) {
      await conn.end();
      return NextResponse.json({ error: 'User already exists' }, { status: 409 });
    }

    const passwordHash = await bcrypt.hash(password, 12);
    await conn.execute(
      'INSERT INTO users (username, email, password_hash, role_id) VALUES (?, ?, ?, 3)',
      [username, email, passwordHash]
    );
    await conn.end();

    return NextResponse.json({ message: 'User created' }, { status: 201 });
  } catch (error) {
    console.error('Register error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
