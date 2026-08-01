'use client';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const COLORS: Record<string, string> = {
  green: '#4CAF50', yellow: '#FF9800', red: '#F44336', grey: '#9E9E9E', black: '#212121', unknown: '#E0E0E0',
};

export default function StatusChart({ data }: { data: Record<string, number> }) {
  const chartData = Object.entries(data || {}).map(([name, value]) => ({ name, value }));

  if (chartData.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie data={chartData} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
          paddingAngle={2} dataKey="value">
          {chartData.map((entry) => (
            <Cell key={entry.name} fill={COLORS[entry.name] || '#E0E0E0'} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
