'use client';
import { Box, Typography } from '@mui/material';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';

export interface ChartSpec {
  type?: 'bar' | 'pie' | 'line';
  title?: string;
  data?: { name: string; value: number }[];
  xKey?: string;
  yKey?: string;
  color?: string;
}

const COLORS = ['#1976d2', '#4caf50', '#ff9800', '#f44336', '#9c27b0', '#00bcd4', '#795548', '#607d8b'];

export default function ChartBlock({ spec }: { spec: ChartSpec }) {
  const data = Array.isArray(spec?.data) ? spec.data : [];
  if (data.length === 0) return null;
  const xKey = spec.xKey || 'name';
  const yKey = spec.yKey || 'value';

  return (
    <Box sx={{ my: 1.5, p: 1.5, border: 1, borderColor: 'divider', borderRadius: 2, bgcolor: 'background.paper' }}>
      {spec.title && <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 700 }}>{spec.title}</Typography>}
      <Box sx={{ width: '100%', height: 240 }}>
        <ResponsiveContainer width="100%" height="100%">
          {spec.type === 'pie' ? (
            <PieChart>
              <Pie data={data} dataKey={yKey} nameKey={xKey} cx="50%" cy="50%" outerRadius={85} label>
                {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          ) : spec.type === 'line' ? (
            <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} fontSize={11} />
              <YAxis fontSize={11} allowDecimals={false} />
              <Tooltip />
              <Line type="monotone" dataKey={yKey} stroke={spec.color || COLORS[0]} strokeWidth={2} />
            </LineChart>
          ) : (
            <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey={xKey} fontSize={11} />
              <YAxis fontSize={11} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey={yKey} fill={spec.color || COLORS[0]} radius={[3, 3, 0, 0]}>
                {data.map((_, i) => <Cell key={i} fill={spec.color || COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </Box>
    </Box>
  );
}
