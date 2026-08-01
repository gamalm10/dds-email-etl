import mysql from 'mysql2/promise';

const pool = mysql.createPool({
  host: process.env.MARIA_HOST || 'localhost',
  port: parseInt(process.env.MARIA_PORT || '3307'),
  user: process.env.MARIA_USER || 'dds',
  password: process.env.MARIA_PASSWORD || 'ddspass',
  database: process.env.MARIA_DATABASE || 'dds',
  waitForConnections: true,
  connectionLimit: 10,
});

export async function query(sql: string, params?: any[]) {
  const [rows] = await pool.execute(sql, params);
  return rows;
}

export { pool };
