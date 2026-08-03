'use client';

import { Card, CardContent, Typography, Chip, Skeleton, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';
import CheckCircle from '@mui/icons-material/CheckCircle';
import Schedule from '@mui/icons-material/Schedule';
import Person from '@mui/icons-material/Person';

interface Props {
  history: any;
  loading: boolean;
}

export default function TasksPanel({ history, loading }: Props) {
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Skeleton variant="text" width={120} height={32} />
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rectangular" height={48} sx={{ mb: 1, borderRadius: 1 }} />
          ))}
        </CardContent>
      </Card>
    );
  }

  const tasks = history?.tasks || [];

  if (tasks.length === 0) {
    return null;
  }

  const openTasks = tasks.filter((t: any) => t.status === 'open');
  const resolvedTasks = tasks.filter((t: any) => t.status === 'resolved');

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Tasks ({openTasks.length} open, {resolvedTasks.length} resolved)
        </Typography>
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Assigned</TableCell>
                <TableCell>Deadline</TableCell>
                <TableCell>Priority</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.map((t: any, i: number) => (
                <TableRow key={i}>
                  <TableCell>
                    <Chip
                      size="small"
                      icon={t.status === 'resolved' ? <CheckCircle /> : <Schedule />}
                      label={t.status}
                      color={t.status === 'resolved' ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell>{t.description}</TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Person fontSize="small" />
                      {t.assigned_to || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>{t.deadline || '-'}</TableCell>
                  <TableCell>
                    {t.priority && (
                      <Chip
                        size="small"
                        label={t.priority}
                        color={t.priority === 'high' ? 'error' : t.priority === 'medium' ? 'warning' : 'default'}
                      />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );
}
