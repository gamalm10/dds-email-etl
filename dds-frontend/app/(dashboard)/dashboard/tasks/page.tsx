'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Typography, Card, Chip, IconButton, CircularProgress } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Refresh } from '@mui/icons-material';

export default function TasksPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = () => {
    setLoading(true);
    fetch('/api/v1/dashboard/tasks').then(r => r.json()).then(d => setTasks(Array.isArray(d) ? d : [])).finally(() => setLoading(false));
  };
  useEffect(() => { fetchTasks(); }, []);

  const columns: GridColDef[] = [
    { field: 'description', headerName: 'Task', flex: 1, minWidth: 200 },
    { field: 'brand_category', headerName: 'Brand', width: 150, renderCell: (p: any) => <Typography variant="body2" sx={{ cursor: 'pointer', color: 'primary.main' }} onClick={() => router.push(`/brands/${p.row.brand_id}`)}>{p.value}</Typography> },
    { field: 'assigned_to', headerName: 'Assignee', width: 120 },
    { field: 'priority', headerName: 'Priority', width: 80, renderCell: (p: any) => <Chip label={p.value} size="small" color={p.value === 'high' ? 'error' : p.value === 'low' ? 'default' : 'warning'} /> },
    { field: 'deadline', headerName: 'Deadline', width: 110 },
    { field: 'category', headerName: 'Category', width: 120 },
    { field: 'report_date', headerName: 'Report', width: 110 },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Tasks <Chip label={tasks.length} size="small" color="warning" /></Typography>
        <IconButton onClick={fetchTasks}><Refresh /></IconButton>
      </Box>
      <Card>
        <DataGrid rows={tasks} columns={columns} getRowId={(row) => row.task_id} loading={loading} autoHeight
          pageSizeOptions={[25, 50, 100]} initialState={{ pagination: { paginationModel: { pageSize: 50 } } }}
          onRowClick={(p) => router.push(`/reports/${p.row.report_id}`)}
          sx={{ border: 'none', '& .MuiDataGrid-row': { cursor: 'pointer' } }} disableRowSelectionOnClick />
      </Card>
    </Box>
  );
}
