'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box, Card, CardContent, Typography, Chip, TextField, MenuItem, Grid, IconButton,
} from '@mui/material';
import { Refresh, Search, FilterList, PictureAsPdf, TableChart } from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import api from '@/lib/api';
import type { ReportSummary } from '@/types/report';

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

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

  const columns: GridColDef[] = [
    { field: 'id', headerName: 'ID', width: 70 },
    {
      field: 'processing_status', headerName: 'Status', width: 110,
      renderCell: (params) => <Chip label={params.value} size="small" sx={{ bgcolor: getStatusColor(params.value), color: 'white' }} />,
    },
    { field: 'subject', headerName: 'Subject', flex: 1, minWidth: 200 },
    { field: 'report_date', headerName: 'Date', width: 120 },
    { field: 'item_count', headerName: 'Items', width: 80, type: 'number' },
    { field: 'task_count', headerName: 'Tasks', width: 80, type: 'number' },
    { field: 'insight_count', headerName: 'Insights', width: 90, type: 'number' },
    {
      field: 'created_at', headerName: 'Created', width: 110,
      valueFormatter: (params) => params ? new Date(params).toLocaleDateString() : '',
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
        </CardContent>
      </Card>

      <Card>
        <DataGrid
          rows={filtered}
          columns={columns}
          loading={loading}
          pageSizeOptions={[10, 25, 50]}
          initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
          onRowClick={(params) => router.push(`/reports/${params.id}`)}
          sx={{ border: 'none', '& .MuiDataGrid-row': { cursor: 'pointer' } }}
          autoHeight
          disableRowSelectionOnClick
        />
      </Card>
    </Box>
  );
}
