'use client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Box, Typography, Card, Chip, IconButton, ToggleButtonGroup, ToggleButton } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { Refresh } from '@mui/icons-material';
import api from '@/lib/api';

const ASSIGNEES = ['All', 'Nancy', 'Max', 'Amir', 'Weheba', 'Haytham'];

export default function TasksPage() {
  const router = useRouter();
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [assignee, setAssignee] = useState('All');

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const params = assignee !== 'All' ? `?assigned_to=${encodeURIComponent(assignee)}` : '';
      const { data } = await api.get(`v1/dashboard/tasks${params}`);
      setTasks(Array.isArray(data) ? data : []);
    } catch { setTasks([]); }
    finally { setLoading(false); }
  }, [assignee]);

  useEffect(() => { fetch(); }, [fetch]);

  const byAssignee = ASSIGNEES.slice(1).map(a => ({
    name: a,
    count: tasks.filter(t => t.assigned_to === a).length,
  }));

  const columns: GridColDef[] = [
    { field: 'description', headerName: 'Task', flex: 1, minWidth: 200 },
    { field: 'brand_category', headerName: 'Brand/Category', width: 150, renderCell: (p: any) => <Typography variant="body2" sx={{ cursor: 'pointer', color: 'primary.main' }} onClick={() => router.push(`/brands/${p.row.brand_id}`)}>{p.value}</Typography> },
    { field: 'assigned_to', headerName: 'Assignee', width: 110 },
    { field: 'priority', headerName: 'Priority', width: 80, renderCell: (p: any) => <Chip label={p.value} size="small" color={p.value === 'high' ? 'error' : p.value === 'low' ? 'default' : 'warning'} /> },
    { field: 'is_resolved', headerName: 'Status', width: 90, renderCell: (p: any) => p.value ? <Chip label="Done" size="small" color="success" /> : <Chip label="Open" size="small" color="warning" /> },
    { field: 'report_date', headerName: 'Request Date', width: 120 },
    { field: 'deadline', headerName: 'Deadline', width: 120 },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Tasks <Chip label={tasks.length} size="small" color="warning" /></Typography>
        <IconButton onClick={fetch}><Refresh /></IconButton>
      </Box>

      <Card sx={{ mb: 3, p: 2 }}>
        <Typography variant="subtitle2" mb={1}>Filter by Assignee</Typography>
        <ToggleButtonGroup value={assignee} exclusive onChange={(_, v) => v && setAssignee(v)} size="small">
          {ASSIGNEES.map(a => (
            <ToggleButton key={a} value={a}>{a} {a !== 'All' && `(${byAssignee.find(b => b.name === a)?.count || 0})`}</ToggleButton>
          ))}
        </ToggleButtonGroup>
      </Card>

      <Card>
        <DataGrid rows={tasks} columns={columns} getRowId={(r: any) => r.task_id} loading={loading} autoHeight
          pageSizeOptions={[25, 50, 100]} initialState={{ pagination: { paginationModel: { pageSize: 50 } } }}
          onRowClick={(p: any) => router.push(`/tasks/${p.row.task_id}`)}
          sx={{ border: 'none', '& .MuiDataGrid-row': { cursor: 'pointer' } }} disableRowSelectionOnClick />
      </Card>
    </Box>
  );
}
