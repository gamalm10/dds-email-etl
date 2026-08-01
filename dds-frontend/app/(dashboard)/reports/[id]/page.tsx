'use client';
import { useEffect, useState, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Box, Card, CardContent, Typography, Chip, Tabs, Tab, Grid, IconButton, Button, CircularProgress,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Accordion, AccordionSummary, AccordionDetails,
} from '@mui/material';
import {
  ArrowBack, Refresh, PictureAsPdf, TableChart, ExpandMore, Delete, Replay,
  Warning, CheckCircle, Error as ErrorIcon, Schedule, Assignment, Gavel, TrendingUp, Email,
} from '@mui/icons-material';
import api from '@/lib/api';
import InsightCard from '@/components/insights/InsightCard';
import ExecutiveSummary from '@/components/reports/ExecutiveSummary';
import DeltaSection from '@/components/reports/DeltaSection';
import OriginalEmailModal from '@/components/reports/OriginalEmailModal';
import { exportReportPDF, exportReportExcel } from '@/lib/export';
import type { Report, RiskLanguage, PaymentTerm, LeadTime, Negotiation } from '@/types/report';

export default function ReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [report, setReport] = useState<Report | null>(null);
  const [risks, setRisks] = useState<RiskLanguage[]>([]);
  const [payments, setPayments] = useState<PaymentTerm[]>([]);
  const [leads, setLeads] = useState<LeadTime[]>([]);
  const [negos, setNegos] = useState<Negotiation[]>([]);
  const [clearance, setClearance] = useState<any[]>([]);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState(0);
  const [originalOpen, setOriginalOpen] = useState(false);

  const handleDelete = async () => {
    if (!confirm(`Delete report #${params.id}? This cannot be undone.`)) return;
    try { await api.delete(`v1/reports/${params.id}`); router.push('/reports'); }
    catch (err: any) { alert(`Delete failed: ${err.message || err}`); }
  };

  const handleReprocess = async () => {
    setLoading(true);
    try {
      await api.post(`v1/reports/${params.id}/reprocess`);
      fetchReport();
    } catch (err: any) { alert(`Reprocess failed: ${err.message || err}`); }
    finally { setLoading(false); }
  };

  const fetchReport = useCallback(async () => {
    setLoading(true);
    try {
      const id = params.id as string;
      const [rep, riskRes, payRes, leadRes, negoRes] = await Promise.all([
        api.get(`v1/reports/${id}`),
        api.get(`v1/reports/${id}/risks`).catch(() => ({ data: [] })),
        api.get(`v1/reports/${id}/payment-terms`).catch(() => ({ data: [] })),
        api.get(`v1/reports/${id}/lead-times`).catch(() => ({ data: [] })),
        api.get(`v1/reports/${id}/negotiations`).catch(() => ({ data: [] })),
      ]);
      setReport(rep.data);
      setRisks(riskRes.data);
      setPayments(payRes.data);
      setLeads(leadRes.data);
      setNegos(negoRes.data);
      api.get(`v1/reports/${id}/clearance-materials`).then(({ data }: {data:any}) => setClearance(Array.isArray(data) ? data : [])).catch(() => setClearance([]));
      api.get(`v1/reports/${id}/summary`).then(({ data: d }) => setSummaryData(d)).catch(() => {});
    } catch (err) {
      console.error('Failed to load report:', err);
    } finally {
      setLoading(false);
    }
  }, [params.id]);

  useEffect(() => { fetchReport(); }, [fetchReport]);

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}><CircularProgress /></Box>;
  if (!report) return <Typography>Report not found</Typography>;

  const getAvailabilityColor = (s: string) => {
    const colors: Record<string, string> = { green: '#4CAF50', yellow: '#FF9800', red: '#F44336', grey: '#9E9E9E', black: '#212121', unknown: '#E0E0E0' };
    return colors[s] || '#E0E0E0';
  };

  const getSeverityColor = (s: string) => {
    const colors: Record<string, string> = { critical: '#F44336', major: '#FF9800', minor: '#2196F3', info: '#9E9E9E' };
    return colors[s] || '#9E9E9E';
  };

  const riskCategories = risks.reduce((acc: Record<string, number>, r) => {
    acc[r.category] = (acc[r.category] || 0) + 1;
    return acc;
  }, {});

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => router.push('/reports')}><ArrowBack /></IconButton>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h5">{report.subject || `Report #${report.id}`}</Typography>
          <Typography variant="body2" color="text.secondary">
            {report.report_date} · {report.sender} · Risk Score: {report.risk_score}
          </Typography>
        </Box>
        <Chip label={report.processing_status} color={report.processing_status === 'completed' ? 'success' : 'default'} />
        <IconButton onClick={() => exportReportPDF(report, risks, payments, leads)} title="Export PDF"><PictureAsPdf /></IconButton>
        <IconButton onClick={() => exportReportExcel(report, risks)} title="Export Excel"><TableChart /></IconButton>
        <IconButton onClick={() => setOriginalOpen(true)} title="View Original Email" sx={{ color: 'info.main' }}><Email /></IconButton>
        <IconButton onClick={handleReprocess} title="Reprocess" color="primary"><Replay /></IconButton>
        <IconButton onClick={handleDelete} title="Delete Report" color="error"><Delete /></IconButton>
        <IconButton onClick={fetchReport}><Refresh /></IconButton>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
          <Box><Typography variant="h6">{report.items.length}</Typography><Typography variant="caption">Items</Typography></Box>
          <Box><Typography variant="h6">{report.insights.length}</Typography><Typography variant="caption">Insights</Typography></Box>
          <Box><Typography variant="h6">{report.priority_actions.length}</Typography><Typography variant="caption">Actions</Typography></Box>
          <Box><Typography variant="h6">{risks.length}</Typography><Typography variant="caption">Risks</Typography></Box>
          <Box><Typography variant="h6">{report.risk_score}</Typography><Typography variant="caption">Risk Score</Typography></Box>
          {report.risk_category && <Chip label={report.risk_category} color="warning" size="small" sx={{ alignSelf: 'center' }} />}
        </CardContent>
      </Card>

      {summaryData && (
        <ExecutiveSummary data={summaryData} onDrilldown={(type) => {
          if (type === 'tasks') setTab(4);
        }} />
      )}

      <DeltaSection reportId={Number(params.id)} />

      <Card>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
          <Tab label="Items" />
          <Tab label="Insights & Risks" />
          <Tab label="Actions" />
          <Tab label="Timeline & Payments" />
          <Tab label="Additional" />
          {clearance.length > 0 && <Tab label={`Clearance (${clearance.length})`} />}
        </Tabs>

        {/* Tab 1: Items */}
        {tab === 0 && (
          <Box sx={{ p: 2, overflow: 'auto' }}>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Brand/Category</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Vendor</TableCell>
                    <TableCell>Milestone</TableCell>
                    <TableCell>Shipment</TableCell>
                    <TableCell>Qty</TableCell>
                    <TableCell>Financial</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {report.items.map((item) => (
                    <TableRow key={item.id} hover>
                      <TableCell sx={{ cursor: 'pointer' }} onClick={() => router.push(`/brands/${item.brand.id}`)}>
                        <Typography variant="body2" fontWeight={600} color="primary">{item.brand.brand_category}</Typography>
                        <Typography variant="caption">{item.brand.division}</Typography>
                      </TableCell>
                      <TableCell><Chip label={item.availability_status} size="small" sx={{ bgcolor: getAvailabilityColor(item.availability_status), color: 'white', minWidth: 60 }} /></TableCell>
                      <TableCell>{item.vendor || '-'}</TableCell>
                      <TableCell>{item.milestone || '-'}</TableCell>
                      <TableCell>{item.shipment_bis || '-'}</TableCell>
                      <TableCell>{item.quantity_text || '-'}</TableCell>
                      <TableCell>{item.financial_text || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Tab 2: Insights & Risks */}
        {tab === 1 && (
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" mb={2}>Insights ({report.insights.length})</Typography>
            <Grid container spacing={2} mb={4}>
              {report.insights.map((ins) => (
                <Grid item xs={12} md={6} key={ins.id}>
                  <InsightCard insight={ins} compact />
                </Grid>
              ))}
            </Grid>

            <Typography variant="h6" mb={2}>Risk Analysis ({risks.length})</Typography>
            <Grid container spacing={2} mb={2}>
              {Object.entries(riskCategories).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([cat, count]) => (
                <Grid item xs={6} md={3} key={cat}>
                  <Card variant="outlined">
                    <CardContent sx={{ textAlign: 'center', py: 2 }}>
                      <Typography variant="h5" color={count > 10 ? 'error.main' : count > 5 ? 'warning.main' : 'text.primary'}>{count}</Typography>
                      <Typography variant="caption" textTransform="capitalize">{cat.replace(/_/g, ' ')}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Phrase</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>Score</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {risks.slice(0, 20).map((r) => (
                    <TableRow key={r.id} hover>
                      <TableCell>{r.phrase}</TableCell>
                      <TableCell><Chip label={r.category} size="small" variant="outlined" /></TableCell>
                      <TableCell><Chip label={r.severity_score} size="small" color={r.severity_score >= 3 ? 'error' : r.severity_score >= 2 ? 'warning' : 'default'} /></TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Tab 3: Actions */}
        {tab === 2 && (
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" mb={2}>Priority Actions</Typography>
            <TableContainer component={Paper} variant="outlined" sx={{ mb: 4 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Person</TableCell>
                    <TableCell>Action</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>Urgency</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {report.priority_actions.map((a) => (
                    <TableRow key={a.id} hover sx={{ cursor: 'pointer' }} onClick={() => router.push(`/actions/${a.id}`)}>
                      <TableCell><Chip label={a.person} size="small" color="primary" variant="outlined" /></TableCell>
                      <TableCell>{a.action}</TableCell>
                      <TableCell>{a.category || '-'}</TableCell>
                      <TableCell><Chip label={a.urgency || 'medium'} size="small" color={a.urgency === 'high' ? 'error' : a.urgency === 'low' ? 'default' : 'warning'} /></TableCell>
                    </TableRow>
                  ))}
                  {report.priority_actions.length === 0 && (
                    <TableRow><TableCell colSpan={4} align="center">No priority actions extracted</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" mb={2}>Negotiations</Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Type</TableCell>
                    <TableCell>Percentage</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {negos.map((n) => (
                    <TableRow key={n.id} hover>
                      <TableCell>{n.type}</TableCell>
                      <TableCell>{n.percentage ? `${n.percentage}%` : '-'}</TableCell>
                      <TableCell><Chip label={n.status} size="small" color={n.status === 'agreed' ? 'success' : n.status === 'rejected' ? 'error' : 'warning'} /></TableCell>
                    </TableRow>
                  ))}
                  {negos.length === 0 && <TableRow><TableCell colSpan={3} align="center">No negotiations extracted</TableCell></TableRow>}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Tab 4: Timeline & Payments */}
        {tab === 3 && (
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" mb={2}>Sales Timeline</Typography>
            {report.thread_summary?.sales_timeline && (
              <Card variant="outlined" sx={{ mb: 4, p: 2 }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                  {(() => {
                    try { return JSON.stringify(JSON.parse(report.thread_summary.sales_timeline), null, 2); }
                    catch { return report.thread_summary.sales_timeline; }
                  })()}
                </Typography>
              </Card>
            )}

            <Typography variant="h6" mb={2}>Key Highlights</Typography>
            {report.thread_summary?.key_highlights && (
              <Card variant="outlined" sx={{ mb: 4, p: 2 }}>
                {(() => {
                  try { const h = JSON.parse(report.thread_summary.key_highlights); return Array.isArray(h) ? h.map((s: string, i: number) => <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>• {s}</Typography>) : <Typography variant="body2">{report.thread_summary?.key_highlights}</Typography>; }
                  catch { return <Typography variant="body2">{report.thread_summary?.key_highlights}</Typography>; }
                })()}
              </Card>
            )}

            <Typography variant="h6" mb={2}>Payment Terms</Typography>
            <TableContainer component={Paper} variant="outlined" sx={{ mb: 4 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Method</TableCell>
                    <TableCell>Deposit</TableCell>
                    <TableCell>Balance</TableCell>
                    <TableCell>Expected Date</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {payments.map((p) => (
                    <TableRow key={p.id} hover>
                      <TableCell><Chip label={p.payment_method} size="small" /></TableCell>
                      <TableCell>{p.deposit_pct ? `${p.deposit_pct}%` : '-'}</TableCell>
                      <TableCell>{p.balance_pct ? `${p.balance_pct}%` : '-'}</TableCell>
                      <TableCell>{p.expected_date || '-'}</TableCell>
                    </TableRow>
                  ))}
                  {payments.length === 0 && <TableRow><TableCell colSpan={4} align="center">No payment terms extracted</TableCell></TableRow>}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" mb={2}>Lead Times</Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Days</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {leads.map((l) => (
                    <TableRow key={l.id} hover>
                      <TableCell>{l.days} days</TableCell>
                      <TableCell><Chip label={l.status} size="small" /></TableCell>
                    </TableRow>
                  ))}
                  {leads.length === 0 && <TableRow><TableCell colSpan={2} align="center">No lead times extracted</TableCell></TableRow>}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}

        {/* Tab 5: Additional */}
        {tab === 4 && (
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" mb={2}>Tasks</Typography>
            <TableContainer component={Paper} variant="outlined" sx={{ mb: 4 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Task</TableCell>
                    <TableCell>Assignee</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell>Deadline</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {report.items.flatMap((item) => item.tasks).slice(0, 30).map((t) => (
                    <TableRow key={t.id} hover sx={{ cursor: 'pointer' }} onClick={() => router.push(`/tasks/${t.id}`)}>
                      <TableCell>{t.task_description}</TableCell>
                      <TableCell>{t.assigned_to || '-'}</TableCell>
                      <TableCell>{t.task_category || '-'}</TableCell>
                      <TableCell><Chip label={t.priority} size="small" color={t.priority === 'high' ? 'error' : t.priority === 'low' ? 'default' : 'warning'} /></TableCell>
                      <TableCell>{t.deadline || '-'}</TableCell>
                      <TableCell>{t.is_resolved ? <Chip label="Done" size="small" color="success" /> : <Chip label="Open" size="small" color="warning" />}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" mb={2}>Report Metadata</Typography>
            <Card variant="outlined" sx={{ p: 2, mb: 4 }}>
              <Grid container spacing={2}>
                <Grid item xs={6} md={3}><Typography variant="caption">ID</Typography><Typography variant="body2">{report.id}</Typography></Grid>
                <Grid item xs={6} md={3}><Typography variant="caption">Subject</Typography><Typography variant="body2">{report.subject}</Typography></Grid>
                <Grid item xs={6} md={3}><Typography variant="caption">Date</Typography><Typography variant="body2">{report.report_date}</Typography></Grid>
                <Grid item xs={6} md={3}><Typography variant="caption">Sender</Typography><Typography variant="body2">{report.sender}</Typography></Grid>
                <Grid item xs={6} md={3}><Typography variant="caption">Status</Typography><Typography variant="body2">{report.processing_status}</Typography></Grid>
                <Grid item xs={6} md={3}><Typography variant="caption">Risk Score</Typography><Typography variant="body2">{report.risk_score}</Typography></Grid>
                <Grid item xs={6} md={3}><Typography variant="caption">Risk Category</Typography><Typography variant="body2">{report.risk_category || '-'}</Typography></Grid>
                <Grid item xs={6} md={3}><Typography variant="caption">Received</Typography><Typography variant="body2">{new Date(report.received_at).toLocaleString()}</Typography></Grid>
              </Grid>
            </Card>

            <Typography variant="h6" mb={2}>Thread Summary</Typography>
            {report.thread_summary ? (
              <Card variant="outlined" sx={{ p: 2 }}>
                <Grid container spacing={2}>
                  <Grid item xs={4}><Typography variant="caption">Anomalies</Typography><Typography variant="h6">{report.thread_summary.total_anomalies}</Typography></Grid>
                  <Grid item xs={4}><Typography variant="caption">Health</Typography><Chip label={report.thread_summary.overall_health || 'unknown'} size="small" /></Grid>
                  <Grid item xs={4}><Typography variant="caption">Risks</Typography><Typography variant="body2">{report.thread_summary.priority_matrix || '-'}</Typography></Grid>
                </Grid>
              </Card>
            ) : <Typography variant="body2" color="text.secondary">No thread summary available</Typography>}
          </Box>
        )}

        {/* Tab 5: Clearance */}
        {tab === 5 && clearance.length > 0 && (
          <Box sx={{ p: 2 }}>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Material Code</TableCell>
                    <TableCell>Category</TableCell>
                    <TableCell>Arabic Description</TableCell>
                    <TableCell>Qty</TableCell>
                    <TableCell>Other Qty</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {clearance.map((c: any) => (
                    <TableRow key={c.id} hover>
                      <TableCell><Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{c.material_code}</Typography></TableCell>
                      <TableCell>{c.description || '-'}</TableCell>
                      <TableCell>{c.description_ar || '-'}</TableCell>
                      <TableCell>{c.quantity?.toLocaleString() || '-'}</TableCell>
                      <TableCell>{c.quantity_other ? c.quantity_other.toLocaleString() : '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        )}
      </Card>
      <OriginalEmailModal open={originalOpen} reportId={Number(params.id)} onClose={() => setOriginalOpen(false)} />
    </Box>
  );
}
