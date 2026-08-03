'use client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box, Card, CardContent, Typography, Chip, TextField, MenuItem, Grid, IconButton,
  Button, Snackbar, Alert, Tooltip, CircularProgress,
} from '@mui/material';
import {
  Refresh, Search, PictureAsPdf, TableChart, Email, Replay, Delete,
} from '@mui/icons-material';
import { DataGrid, GridColDef, GridRowSelectionModel } from '@mui/x-data-grid';
import api from '@/lib/api';
import OriginalEmailModal from '@/components/reports/OriginalEmailModal';
import { exportReportPDF, exportReportExcel } from '@/lib/export';
import type { ReportSummary } from '@/types/report';

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedIds, setSelectedIds] = useState<GridRowSelectionModel>([]);
  const [originalReportId, setOriginalReportId] = useState<number | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({ open: false, message: '', severity: 'success' });

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await api.get('v1/reports');
      setReports(res.data);
    } catch (err) {
      console.error('Failed to fetch reports:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchReports(); }, []);

  const filtered = reports.filter((r) => {
    if (search && !r.subject?.toLowerCase().includes(search.toLowerCase())) return false;
    if (statusFilter && r.processing_status !== statusFilter) return false;
    return true;
  });

  const getStatusColor = (s: string) => {
    const colors: Record<string, string> = { completed: '#4CAF50', failed: '#F44336', processing: '#FF9800', pending: '#9E9E9E' };
    return colors[s] || '#9E9E9E';
  };

  const handleDelete = async (id: number) => {
    if (!confirm(`Delete report #${id}? This cannot be undone.`)) return;
    setActionLoading(id);
    try {
      await api.delete(`v1/reports/${id}`);
      setReports((prev) => prev.filter((r) => r.id !== id));
    } catch (err: any) {
      setSnackbar({ open: true, message: `Delete failed: ${err.message || err}`, severity: 'error' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleReprocess = async (id: number) => {
    setActionLoading(id);
    try {
      await api.post(`v1/reports/${id}/reprocess`);
      setSnackbar({ open: true, message: `Report #${id} reprocessed`, severity: 'success' });
      fetchReports();
    } catch (err: any) {
      setSnackbar({ open: true, message: `Reprocess failed: ${err.response?.data?.detail || err.message}`, severity: 'error' });
    } finally {
      setActionLoading(null);
    }
  };

  const fetchFullReport = async (id: number) => {
    const [rep, riskRes, payRes, leadRes] = await Promise.all([
      api.get(`v1/reports/${id}`),
      api.get(`v1/reports/${id}/risks`).catch(() => ({ data: [] })),
      api.get(`v1/reports/${id}/payment-terms`).catch(() => ({ data: [] })),
      api.get(`v1/reports/${id}/lead-times`).catch(() => ({ data: [] })),
    ]);
    return { report: rep.data, risks: riskRes.data, payments: payRes.data, leads: leadRes.data };
  };

  const handleExportPDF = async (id: number) => {
    setActionLoading(id);
    try {
      const { report, risks, payments, leads } = await fetchFullReport(id);
      exportReportPDF(report, risks, payments, leads);
    } catch (err: any) {
      setSnackbar({ open: true, message: 'Export PDF failed', severity: 'error' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleExportExcel = async (id: number) => {
    setActionLoading(id);
    try {
      const { report, risks } = await fetchFullReport(id);
      exportReportExcel(report, risks);
    } catch (err: any) {
      setSnackbar({ open: true, message: 'Export Excel failed', severity: 'error' });
    } finally {
      setActionLoading(null);
    }
  };

  const handleBulkDelete = async () => {
    if (!confirm(`Delete ${selectedIds.length} report(s)? This cannot be undone.`)) return;
    setBulkLoading(true);
    let failed = 0;
    for (const id of selectedIds) {
      try {
        await api.delete(`v1/reports/${Number(id)}`);
      } catch {
        failed++;
      }
    }
    setBulkLoading(false);
    setSelectedIds([]);
    fetchReports();
    setSnackbar({ open: true, message: `Deleted ${selectedIds.length - failed} report(s)${failed ? `, ${failed} failed` : ''}`, severity: failed ? 'error' : 'success' });
  };

  const handleBulkReprocess = async () => {
    setBulkLoading(true);
    let done = 0;
    let failed = 0;
    for (const id of selectedIds) {
      try {
        await api.post(`v1/reports/${Number(id)}/reprocess`);
        done++;
      } catch {
        failed++;
      }
    }
    setBulkLoading(false);
    setSelectedIds([]);
    fetchReports();
    setSnackbar({ open: true, message: `Reprocessed ${done} report(s)${failed ? `, ${failed} failed` : ''}`, severity: failed ? 'error' : 'success' });
  };

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    {
      field: 'processing_status', headerName: 'Status', width: 110,
      renderCell: (params) => <Chip label={params.value} size="small" sx={{ bgcolor: getStatusColor(params.value), color: 'white' }} />,
    },
    { field: 'subject', headerName: 'Subject', flex: 1, minWidth: 200 },
    { field: 'report_date', headerName: 'Date', width: 120 },
    { field: 'item_count', headerName: 'Items', width: 70, type: 'number' },
    { field: 'task_count', headerName: 'Tasks', width: 70, type: 'number' },
    { field: 'insight_count', headerName: 'Insights', width: 80, type: 'number' },
    {
      field: 'created_at', headerName: 'Created', width: 110,
      valueFormatter: (params: any) => params ? new Date(params).toLocaleDateString() : '',
    },
    {
      field: 'actions', headerName: 'Actions', width: 210, sortable: false, filterable: false,
      renderCell: (params) => {
        const id = params.row.id;
        const isLoading = actionLoading === id;
        return (
          <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center' }}>
            {isLoading ? (
              <CircularProgress size={20} sx={{ mx: 1 }} />
            ) : (
              <>
                <Tooltip title="Original Email">
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); setOriginalReportId(id); }}>
                    <Email fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Reprocess">
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleReprocess(id); }}>
                    <Replay fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Export PDF">
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleExportPDF(id); }}>
                    <PictureAsPdf fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Export Excel">
                  <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleExportExcel(id); }}>
                    <TableChart fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete">
                  <IconButton size="small" color="error" onClick={(e) => { e.stopPropagation(); handleDelete(id); }}>
                    <Delete fontSize="small" />
                  </IconButton>
                </Tooltip>
              </>
            )}
          </Box>
        );
      },
    },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Reports</Typography>
        <IconButton onClick={fetchReports}><Refresh /></IconButton>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField size="small" placeholder="Search reports..." value={search} onChange={(e) => setSearch(e.target.value)}
            sx={{ minWidth: 250 }} InputProps={{ startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} /> }} />
          <TextField size="small" select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} label="Status" sx={{ minWidth: 140 }}>
            <MenuItem value="">All</MenuItem>
            <MenuItem value="completed">Completed</MenuItem>
            <MenuItem value="failed">Failed</MenuItem>
            <MenuItem value="processing">Processing</MenuItem>
            <MenuItem value="pending">Pending</MenuItem>
          </TextField>
          {selectedIds.length > 0 && (
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', ml: 'auto' }}>
              <Typography variant="body2" sx={{ mr: 1 }}>{selectedIds.length} selected</Typography>
              <Button size="small" variant="outlined" startIcon={<Replay />} onClick={handleBulkReprocess} disabled={bulkLoading}>
                Reprocess
              </Button>
              <Button size="small" variant="outlined" color="error" startIcon={<Delete />} onClick={handleBulkDelete} disabled={bulkLoading}>
                Delete
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      <Card>
        <DataGrid
          rows={filtered}
          columns={columns}
          loading={loading}
          checkboxSelection
          rowSelectionModel={selectedIds}
          onRowSelectionModelChange={(ids) => setSelectedIds(ids)}
          pageSizeOptions={[10, 25, 50]}
          initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
          onRowClick={(params) => router.push(`/reports/${params.id}`)}
          sx={{ border: 'none', '& .MuiDataGrid-row': { cursor: 'pointer' } }}
          autoHeight
        />
      </Card>

      {originalReportId !== null && (
        <OriginalEmailModal
          open={true}
          reportId={originalReportId}
          itemCount={0}
          onClose={() => setOriginalReportId(null)}
          onReuploadDone={() => { fetchReports(); setSnackbar({ open: true, message: 'Report re-uploaded', severity: 'success' }); }}
        />
      )}

      <Snackbar open={snackbar.open} autoHideDuration={4000} onClose={() => setSnackbar({ ...snackbar, open: false })} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}>
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>{snackbar.message}</Alert>
      </Snackbar>
    </Box>
  );
}
