'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box, Typography, Card, Chip, IconButton, Tooltip, CircularProgress,
  Grid, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Accordion, AccordionSummary, AccordionDetails,
} from '@mui/material';
import {
  ExpandMore, Email, Replay, Assignment, TaskAlt, Lightbulb, Payments, Gavel,
} from '@mui/icons-material';
import api from '@/lib/api';
import OriginalEmailModal from '@/components/reports/OriginalEmailModal';
import { navigate } from '@/components/common/navigate';

export const getStatusColor = (s: string) => {
  const colors: Record<string, string> = { green: '#4CAF50', yellow: '#FF9800', red: '#F44336', grey: '#9E9E9E', unknown: '#E0E0E0' };
  return colors[s] || '#9E9E9E';
};

const shortDate = (iso?: string) => {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso.slice(5);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const ReportDateTimeline = ({ presentDates }: { presentDates?: string[] }) => {
  if (!presentDates || presentDates.length === 0) return null;
  const present = new Set(presentDates);
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap', mt: 0.5 }}>
      {presentDates.map((d) => (
        <Box
          key={d}
          sx={{
            fontSize: 10,
            px: 0.6,
            py: 0.2,
            borderRadius: '4px',
            bgcolor: present.has(d) ? 'primary.main' : 'transparent',
            color: present.has(d) ? 'primary.contrastText' : 'text.disabled',
            border: '1px solid',
            borderColor: present.has(d) ? 'primary.main' : 'divider',
            whiteSpace: 'nowrap',
          }}
        >
          {shortDate(d)}
        </Box>
      ))}
    </Box>
  );
};

const ItemBox = ({ icon, title, iconColor, children }: { icon: React.ReactNode; title: string; iconColor?: string; children: React.ReactNode }) => (
  <Box sx={{ mb: 1 }}>
    <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
      {icon} {title}
    </Typography>
    {children}
  </Box>
);

export default function ReportTimeline({ reports, onReprocessed }: { reports: any[]; onReprocessed?: () => void }) {
  const router = useRouter();
  const [expanded, setExpanded] = useState<number | null>(null);
  const [originalReport, setOriginalReport] = useState<number | null>(null);
  const [reprocessing, setReprocessing] = useState<number | null>(null);

  const handleReprocess = async (reportId: number) => {
    setReprocessing(reportId);
    try {
      await api.post(`v1/reports/${reportId}/reprocess`);
      onReprocessed?.();
    } catch (err: any) {
      alert(`Reprocess failed: ${err.message || err}`);
    } finally {
      setReprocessing(null);
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {reports?.map((r: any) => {
        const open = expanded === null || expanded === r.report_id;
        return (
          <Card key={r.report_id} variant="outlined">
            <Accordion
              expanded={open}
              onChange={() => setExpanded(open ? null : r.report_id)}
              slotProps={{ transition: { unmountOnExit: true } }}
            >
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, width: '100%', flexWrap: 'wrap' }}>
                  <Typography
                    variant="subtitle1"
                    fontWeight={600}
                    sx={{ cursor: 'pointer', flex: 1, minWidth: 200 }}
                    onClick={(e) => { e.stopPropagation(); navigate(router, `/reports/${r.report_id}`); }}
                  >
                    {r.report_date || '-'} — {r.subject || `Report #${r.report_id}`}
                  </Typography>
                  {r.statuses?.map((s: string) => <Chip key={s} label={s} size="small" sx={{ bgcolor: getStatusColor(s), color: 'white' }} />)}
                  <Chip label={r.processing_status} size="small" variant="outlined" />
                  <Tooltip title="View Original Email">
                    <IconButton size="small" onClick={(e) => { e.stopPropagation(); setOriginalReport(r.report_id); }} sx={{ color: 'info.main' }}>
                      <Email fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Re-process Report">
                    <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleReprocess(r.report_id); }} disabled={reprocessing === r.report_id} color="primary">
                      {reprocessing === r.report_id ? <CircularProgress size={16} /> : <Replay fontSize="small" />}
                    </IconButton>
                  </Tooltip>
                </Box>
              </AccordionSummary>

              <AccordionDetails sx={{ pt: 0 }}>
                {r.items?.length > 0 && (
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Brand/Category</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Milestone</TableCell>
                          <TableCell>ETD</TableCell>
                          <TableCell>ETA</TableCell>
                          <TableCell>Ready for Sale</TableCell>
                          <TableCell>Comments</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {r.items.map((it: any) => (
                          <TableRow key={it.item_id}>
                            <TableCell>{it.brand_category}</TableCell>
                            <TableCell><Chip label={it.availability_status} size="small" sx={{ bgcolor: getStatusColor(it.availability_status), color: 'white' }} /></TableCell>
                            <TableCell>{it.milestone || '-'}</TableCell>
                            <TableCell>{it.etd || '-'}</TableCell>
                            <TableCell>{it.eta || '-'}</TableCell>
                            <TableCell>{it.ready_for_sale || '-'}</TableCell>
                            <TableCell sx={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis' }}>{it.comments_actions || '-'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}

                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {r.actions?.length > 0 && (
                        <ItemBox icon={<Assignment fontSize="small" color="primary" />} title="Actions">
                          {r.actions.map((a: any) => (
                            <Box key={a.id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 0.5 }}>
                                <Chip label={a.person} size="small" color="primary" variant="outlined" />
                                {a.urgency && <Chip label={a.urgency} size="small" color={a.urgency === 'high' ? 'error' : a.urgency === 'medium' ? 'warning' : 'default'} />}
                                {a.category && <Typography variant="caption" color="text.secondary">{a.category}</Typography>}
                              </Box>
                              <Typography variant="body2">{a.action}</Typography>
                              <Typography variant="caption" color="text.secondary">Requested: {a.request_date || a.report_date}</Typography>
                              <ReportDateTimeline presentDates={a.present_dates} />
                            </Box>
                          ))}
                        </ItemBox>
                      )}

                      {r.tasks?.length > 0 && (
                        <ItemBox icon={<TaskAlt fontSize="small" color="secondary" />} title="Tasks">
                          {r.tasks.map((t: any) => (
                            <Box key={t.id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 0.5, flexWrap: 'wrap' }}>
                                {t.is_resolved ? <Chip label="Done" size="small" color="success" /> : <Chip label="Open" size="small" color="warning" />}
                                <Chip label={t.priority} size="small" color={t.priority === 'high' ? 'error' : t.priority === 'low' ? 'default' : 'warning'} />
                                {t.assigned_to && <Typography variant="caption" color="text.secondary">→ {t.assigned_to}</Typography>}
                              </Box>
                              <Typography variant="body2">{t.description}</Typography>
                              <Typography variant="caption" color="text.secondary">Requested: {t.request_date || t.report_date}</Typography>
                              <ReportDateTimeline presentDates={t.present_dates} />
                              {t.deadline && <Typography variant="caption" color="text.secondary">Deadline: {t.deadline}</Typography>}
                            </Box>
                          ))}
                        </ItemBox>
                      )}
                    </Box>
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {r.negotiations?.length > 0 && (
                        <ItemBox icon={<Gavel fontSize="small" color="info" />} title="Negotiations">
                          {r.negotiations.map((n: any) => (
                            <Box key={n.id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 0.5 }}>
                                <Chip label={n.status} size="small" color={n.status === 'accepted' ? 'success' : n.status === 'proposed' ? 'warning' : 'default'} />
                                <Typography variant="body2">{n.type} {n.percentage != null ? `${n.percentage}%` : ''}</Typography>
                              </Box>
                              {n.context && <Typography variant="body2">{n.context}</Typography>}
                              <ReportDateTimeline presentDates={n.present_dates} />
                            </Box>
                          ))}
                        </ItemBox>
                      )}

                      {r.payments?.length > 0 && (
                        <ItemBox icon={<Payments fontSize="small" color="success" />} title="Payments">
                          {r.payments.map((p: any) => (
                            <Box key={p.id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                              <Typography variant="body2">{p.payment_method || '-'}</Typography>
                              {p.deposit_pct != null && <Typography variant="caption" color="text.secondary">Deposit {p.deposit_pct}% / Balance {p.balance_pct}%</Typography>}
                              {p.expected_date && <Typography variant="caption" color="text.secondary">Expected: {p.expected_date}</Typography>}
                              <ReportDateTimeline presentDates={p.present_dates} />
                            </Box>
                          ))}
                        </ItemBox>
                      )}

                      {r.insights?.length > 0 && (
                        <ItemBox icon={<Lightbulb fontSize="small" color="warning" />} title="Insights">
                          {r.insights.map((ins: any) => (
                            <Box key={ins.id} sx={{ mb: 1, p: 1, bgcolor: 'background.default', borderRadius: 1 }}>
                              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 0.5 }}>
                                <Chip label={ins.severity} size="small" color={ins.severity === 'critical' ? 'error' : ins.severity === 'major' ? 'warning' : 'default'} />
                                <Typography variant="caption" color="text.secondary">{ins.type}</Typography>
                              </Box>
                              <Typography variant="body2">{ins.description}</Typography>
                              <Typography variant="caption" color="text.secondary">Requested: {ins.request_date || ins.report_date}</Typography>
                              {ins.impact && <Typography variant="caption" color="text.secondary">Impact: {ins.impact}</Typography>}
                            </Box>
                          ))}
                        </ItemBox>
                      )}
                    </Box>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Card>
        );
      })}
      {(!reports || reports.length === 0) && <Typography color="text.secondary">No reports available</Typography>}

      {originalReport != null && (
        <OriginalEmailModal
          open={originalReport != null}
          reportId={originalReport}
          itemCount={0}
          onClose={() => setOriginalReport(null)}
        />
      )}
    </Box>
  );
}
