'use client';
import { useRouter } from 'next/navigation';
import {
  Box, Typography, Card, CardContent, Chip,
  Grid, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
} from '@mui/material';
import {
  Assignment, TaskAlt, Lightbulb, Payments, Gavel,
} from '@mui/icons-material';

export const getStatusColor = (s: string) => {
  const colors: Record<string, string> = { green: '#4CAF50', yellow: '#FF9800', red: '#F44336', grey: '#9E9E9E', unknown: '#E0E0E0' };
  return colors[s] || '#9E9E9E';
};

export default function ReportTimeline({ reports }: { reports: any[] }) {
  const router = useRouter();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {reports?.map((r: any) => (
        <Card key={r.report_id} variant="outlined">
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2, flexWrap: 'wrap' }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle1" fontWeight={600} sx={{ cursor: 'pointer' }} onClick={() => router.push(`/reports/${r.report_id}`)}>
                  {r.report_date || '-'} — {r.subject || `Report #${r.report_id}`}
                </Typography>
              </Box>
              {r.statuses?.map((s: string) => <Chip key={s} label={s} size="small" sx={{ bgcolor: getStatusColor(s), color: 'white' }} />)}
              <Chip label={r.processing_status} size="small" variant="outlined" />
            </Box>

            {r.items?.length > 0 && (
              <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Brand/Category</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Milestone</TableCell>
                      <TableCell>Shipment</TableCell>
                      <TableCell>Comments</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {r.items.map((it: any) => (
                      <TableRow key={it.item_id}>
                        <TableCell>{it.brand_category}</TableCell>
                        <TableCell><Chip label={it.availability_status} size="small" sx={{ bgcolor: getStatusColor(it.availability_status), color: 'white' }} /></TableCell>
                        <TableCell>{it.milestone || '-'}</TableCell>
                        <TableCell>{it.shipment_bis || '-'}</TableCell>
                        <TableCell sx={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis' }}>{it.comments_actions || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}

            <Grid container spacing={2}>
              {r.actions?.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Assignment fontSize="small" color="primary" /> Actions
                  </Typography>
                  {r.actions.map((a: any) => (
                    <Box key={a.id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 0.5 }}>
                        <Chip label={a.person} size="small" color="primary" variant="outlined" />
                        {a.urgency && <Chip label={a.urgency} size="small" color={a.urgency === 'high' ? 'error' : a.urgency === 'medium' ? 'warning' : 'default'} />}
                        {a.category && <Typography variant="caption" color="text.secondary">{a.category}</Typography>}
                      </Box>
                      <Typography variant="body2">{a.action}</Typography>
                    </Box>
                  ))}
                </Grid>
              )}

              {r.tasks?.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <TaskAlt fontSize="small" color="secondary" /> Tasks
                  </Typography>
                  {r.tasks.map((t: any) => (
                    <Box key={t.id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 0.5, flexWrap: 'wrap' }}>
                        {t.is_resolved ? <Chip label="Done" size="small" color="success" /> : <Chip label="Open" size="small" color="warning" />}
                        <Chip label={t.priority} size="small" color={t.priority === 'high' ? 'error' : t.priority === 'low' ? 'default' : 'warning'} />
                        {t.assigned_to && <Typography variant="caption" color="text.secondary">→ {t.assigned_to}</Typography>}
                      </Box>
                      <Typography variant="body2">{t.description}</Typography>
                      {t.deadline && <Typography variant="caption" color="text.secondary">Deadline: {t.deadline}</Typography>}
                    </Box>
                  ))}
                </Grid>
              )}

              {r.insights?.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Lightbulb fontSize="small" color="warning" /> Insights
                  </Typography>
                  {r.insights.map((ins: any) => (
                    <Box key={ins.id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 0.5 }}>
                        <Chip label={ins.severity} size="small" color={ins.severity === 'critical' ? 'error' : ins.severity === 'major' ? 'warning' : 'default'} />
                        <Typography variant="caption" color="text.secondary">{ins.type}</Typography>
                      </Box>
                      <Typography variant="body2">{ins.description}</Typography>
                      {ins.impact && <Typography variant="caption" color="text.secondary">Impact: {ins.impact}</Typography>}
                    </Box>
                  ))}
                </Grid>
              )}

              {r.payments?.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Payments fontSize="small" color="success" /> Payments
                  </Typography>
                  {r.payments.map((p: any) => (
                    <Box key={p.id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Typography variant="body2">{p.payment_method || '-'}</Typography>
                      {p.deposit_pct != null && <Typography variant="caption" color="text.secondary">Deposit {p.deposit_pct}% / Balance {p.balance_pct}%</Typography>}
                      {p.expected_date && <Typography variant="caption" color="text.secondary">Expected: {p.expected_date}</Typography>}
                    </Box>
                  ))}
                </Grid>
              )}

              {r.negotiations?.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Gavel fontSize="small" color="info" /> Negotiations
                  </Typography>
                  {r.negotiations.map((n: any) => (
                    <Box key={n.id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 0.5 }}>
                        <Chip label={n.status} size="small" color={n.status === 'accepted' ? 'success' : n.status === 'proposed' ? 'warning' : 'default'} />
                        <Typography variant="body2">{n.type} {n.percentage != null ? `${n.percentage}%` : ''}</Typography>
                      </Box>
                      {n.context && <Typography variant="body2">{n.context}</Typography>}
                    </Box>
                  ))}
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      ))}
      {(!reports || reports.length === 0) && <Typography color="text.secondary">No reports available</Typography>}
    </Box>
  );
}
