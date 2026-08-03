'use client';

import { Card, CardContent, Typography, Skeleton } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const STATUS_VALUE: Record<string, number> = {
  green: 4,
  yellow: 3,
  blue: 2,
  red: 1,
  white: 0,
  grey: 0,
  unknown: 0,
};

const STATUS_LABELS = ['', 'Red', 'Blue', 'Yellow', 'Green'];

interface Props {
  history: any;
  loading: boolean;
}

export default function StatusChangeChart({ history, loading }: Props) {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Skeleton variant="text" width={160} height={32} />
          <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 1 }} />
        </CardContent>
      </Card>
    );
  }

  if (!history?.status_history?.length) return null;

  const data = history.status_history
    .map((h: any) => ({
      date: history.reports?.find((r: any) => r.report_id === h.report_id)?.report_date || '',
      current: STATUS_VALUE[h.current] || 0,
      previous: h.previous ? STATUS_VALUE[h.previous] || 0 : undefined,
    }))
    .reverse();

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Status Changes
        </Typography>
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" fontSize={11} />
            <YAxis
              domain={[0, 5]}
              ticks={[0, 1, 2, 3, 4]}
              tickFormatter={(v: number) => STATUS_LABELS[v] || ''}
              fontSize={11}
            />
            <Tooltip
              formatter={(value: number) => [STATUS_LABELS[value] || value, 'Status']}
              labelFormatter={(label: string) => `Date: ${label}`}
            />
            <Line
              type="monotone"
              dataKey="current"
              stroke="#1976d2"
              strokeWidth={2}
              dot={{ r: 4 }}
              name="Status"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
