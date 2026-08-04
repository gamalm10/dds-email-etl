'use client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Typography, Card, TextField, MenuItem, Chip, IconButton } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Refresh } from '@mui/icons-material';
import api from '@/lib/api';

export default function VendorsPage() {
  const router = useRouter();
  const [vendors, setVendors] = useState<any[]>([]);
  const [brands, setBrands] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [brandFilter, setBrandFilter] = useState('');

  const fetchVendors = useCallback(async () => {
    setLoading(true);
    try {
      const params = brandFilter ? `?brand_category=${encodeURIComponent(brandFilter)}` : '';
      const { data } = await api.get(`v1/vendors${params}`);
      setVendors(Array.isArray(data) ? data : []);
    } catch (err) { console.error(err); } finally { setLoading(false); }
  }, [brandFilter]);

  const fetchBrands = useCallback(async () => {
    try {
      const { data } = await api.get('v1/brands');
      setBrands(Array.isArray(data) ? data : []);
    } catch (err) { console.error(err); }
  }, []);

  useEffect(() => { fetchVendors(); }, [fetchVendors]);
  useEffect(() => { fetchBrands(); }, [fetchBrands]);

  const filtered = vendors.filter((v) => {
    if (search && !v.vendor?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const getStatusColor = (s: string) => {
    const colors: Record<string, string> = { green: '#4CAF50', yellow: '#FF9800', red: '#F44336', grey: '#9E9E9E', unknown: '#E0E0E0' };
    return colors[s] || '#9E9E9E';
  };

  const columns: GridColDef[] = [
    { field: 'vendor', headerName: 'Vendor', flex: 1, minWidth: 160 },
    { field: 'brand_count', headerName: 'Brands', width: 90, type: 'number' },
    { field: 'brands', headerName: 'Brand/Category', flex: 1.2, minWidth: 220, renderCell: (p: any) => (Array.isArray(p.value) ? p.value.join(', ') : '') },
    { field: 'latest_status', headerName: 'Status', width: 90, renderCell: (p: any) => <Chip label={p.value} size="small" sx={{ bgcolor: getStatusColor(p.value), color: 'white' }} /> },
    { field: 'latest_milestone', headerName: 'Milestone', width: 150 },
    { field: 'total_reports', headerName: 'Reports', width: 90, type: 'number' },
    { field: 'open_tasks', headerName: 'Open Tasks', width: 100, type: 'number', renderCell: (p: any) => <Chip label={p.value} size="small" color={p.value > 5 ? 'error' : p.value > 0 ? 'warning' : 'default'} /> },
    { field: 'total_insights', headerName: 'Insights', width: 90, type: 'number' },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Vendors</Typography>
        <IconButton onClick={fetchVendors}><Refresh /></IconButton>
      </Box>
      <Card sx={{ mb: 3, p: 2, display: 'flex', gap: 2 }}>
        <TextField size="small" placeholder="Search vendors..." value={search} onChange={(e) => setSearch(e.target.value)} sx={{ minWidth: 250 }} />
        <TextField size="small" select value={brandFilter} onChange={(e) => setBrandFilter(e.target.value)} label="Brand/Category" sx={{ minWidth: 220 }}>
          <MenuItem value="">All</MenuItem>
          {brands.map((b) => <MenuItem key={b.id} value={b.brand_category}>{b.brand_category}</MenuItem>)}
        </TextField>
      </Card>
      <Card>
        <DataGrid rows={filtered} columns={columns} loading={loading} autoHeight getRowId={(r) => r.vendor}
          pageSizeOptions={[25, 50, 100]} initialState={{ pagination: { paginationModel: { pageSize: 50 } } }}
          onRowClick={(p) => router.push(`/vendors/${encodeURIComponent(p.row.vendor)}`)}
          sx={{ border: 'none', '& .MuiDataGrid-row': { cursor: 'pointer' } }} disableRowSelectionOnClick />
      </Card>
    </Box>
  );
}
