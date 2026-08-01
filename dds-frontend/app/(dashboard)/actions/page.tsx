'use client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Typography, Card, Chip, IconButton, ToggleButtonGroup, ToggleButton, CircularProgress } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Refresh } from '@mui/icons-material';
import api from '@/lib/api';

const PERSONS = ['All', 'Nancy', 'Max', 'Amir', 'Weheba'];

export default function ActionsPage() {
  const router = useRouter();
  const [actions, setActions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [person, setPerson] = useState('All');

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const params = person !== 'All' ? `?person=${encodeURIComponent(person)}` : '';
      const { data } = await api.get(`v1/actions${params}`);
      setActions(Array.isArray(data) ? data : []);
    } catch { setActions([]); }
    finally { setLoading(false); }
  }, [person]);

  useEffect(() => { fetch(); }, [fetch]);

  const counts = PERSONS.slice(1).map(p => ({ name: p, count: actions.filter(a => a.person === p).length }));

  const urgencyColors: Record<string, string> = { high: '#F44336', medium: '#FF9800', low: '#4CAF50' };

  const columns: GridColDef[] = [
    { field: 'action', headerName: 'Action', flex: 1, minWidth: 250 },
    { field: 'person', headerName: 'Person', width: 100, renderCell: (p: any) => <Chip label={p.value} size="small" color="primary" variant="outlined" /> },
    { field: 'category', headerName: 'Category', width: 120 },
    { field: 'urgency', headerName: 'Urgency', width: 80, renderCell: (p: any) => <Chip label={p.value} size="small" sx={{ bgcolor: urgencyColors[p.value] || '#9E9E9E', color: 'white' }} /> },
    { field: 'report_date', headerName: 'Report Date', width: 120 },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Actions <Chip label={actions.length} size="small" color="primary" /></Typography>
        <IconButton onClick={fetch}><Refresh /></IconButton>
      </Box>
      <Card sx={{ mb: 3, p: 2 }}>
        <Typography variant="subtitle2" mb={1}>Filter by Person</Typography>
        <ToggleButtonGroup value={person} exclusive onChange={(_, v) => v && setPerson(v)} size="small">
          {PERSONS.map(p => (
            <ToggleButton key={p} value={p}>{p} {p !== 'All' && `(${counts.find(c => c.name === p)?.count || 0})`}</ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Card>
      <Card>
        <DataGrid rows={actions} columns={columns} loading={loading} autoHeight
          pageSizeOptions={[25, 50, 100]} initialState={{ pagination: { paginationModel: { pageSize: 50 } } }}
          onRowClick={(p: any) => router.push(`/actions/${p.row.id}`)}
          sx={{ border: 'none', '& .MuiDataGrid-row': { cursor: 'pointer' } }} disableRowSelectionOnClick />
      </Card>
    </Box>
  );
}
