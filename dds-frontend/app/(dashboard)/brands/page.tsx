'use client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Typography, Card, TextField, MenuItem, Chip, IconButton } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Refresh } from '@mui/icons-material';
import api from '@/lib/api';

export default function BrandsPage() {
  const router = useRouter();
  const [brands, setBrands] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [divisionFilter, setDivisionFilter] = useState('');

  const fetchBrands = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.get('v1/dashboard/brands');
      setBrands(Array.isArray(data) ? data : []);
    } catch (err) { console.error(err); } finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchBrands(); }, [fetchBrands]);

  const filtered = brands.filter((b) => {
    if (search && !b.brand_category?.toLowerCase().includes(search.toLowerCase())) return false;
    if (divisionFilter && b.division !== divisionFilter) return false;
    return true;
  });

  const getStatusColor = (s: string) => {
    const colors: Record<string, string> = { green: '#4CAF50', yellow: '#FF9800', red: '#F44336', grey: '#9E9E9E', unknown: '#E0E0E0' };
    return colors[s] || '#9E9E9E';
  };

  const columns: GridColDef[] = [
    { field: 'brand_category', headerName: 'Brand/Category', flex: 1, minWidth: 180 },
    { field: 'division', headerName: 'Division', width: 120 },
    { field: 'vendor', headerName: 'Vendor', width: 120 },
    { field: 'latest_status', headerName: 'Status', width: 90, renderCell: (p: any) => <Chip label={p.value} size="small" sx={{ bgcolor: getStatusColor(p.value), color: 'white' }} /> },
    { field: 'latest_milestone', headerName: 'Milestone', width: 150 },
    { field: 'total_reports', headerName: 'Reports', width: 90, type: 'number' },
    { field: 'open_tasks', headerName: 'Open Tasks', width: 100, type: 'number', renderCell: (p: any) => <Chip label={p.value} size="small" color={p.value > 5 ? 'error' : p.value > 0 ? 'warning' : 'default'} /> },
    { field: 'total_insights', headerName: 'Insights', width: 90, type: 'number' },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Brands</Typography>
        <IconButton onClick={fetchBrands}><Refresh /></IconButton>
      </Box>
      <Card sx={{ mb: 3, p: 2, display: 'flex', gap: 2 }}>
        <TextField size="small" placeholder="Search brands..." value={search} onChange={(e) => setSearch(e.target.value)} sx={{ minWidth: 250 }} />
        <TextField size="small" select value={divisionFilter} onChange={(e) => setDivisionFilter(e.target.value)} label="Division" sx={{ minWidth: 140 }}>
          <MenuItem value="">All</MenuItem>
          <MenuItem value="Passenger">Passenger</MenuItem>
          <MenuItem value="Battery">Battery</MenuItem>
          <MenuItem value="Diesel">Diesel</MenuItem>
          <MenuItem value="Trucks">Trucks</MenuItem>
          <MenuItem value="PAS">PAS</MenuItem>
        </TextField>
      </Card>
      <Card>
        <DataGrid rows={filtered} columns={columns} loading={loading} autoHeight
          pageSizeOptions={[25, 50, 100]} initialState={{ pagination: { paginationModel: { pageSize: 50 } } }}
          onRowClick={(p) => router.push(`/brands/${p.id}`)}
          sx={{ border: 'none', '& .MuiDataGrid-row': { cursor: 'pointer' } }} disableRowSelectionOnClick />
      </Card>
    </Box>
  );
}
