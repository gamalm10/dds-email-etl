'use client';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function RiskChart({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data || {}).map(([category, count]) => ({
    category: category.replace(/_/g, ' '),
    count,
  })).sort((a, b) => b.count - a.count).slice(0, 10);

  if (chartData.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={250}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 100, right: 20 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis type="number" />
        <YAxis type="category" dataKey="category" tick={{ fontSize: 12 }} />
        <Tooltip />
        <Bar dataKey="count" fill="#F44336" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
