'use client';
import { Dialog, DialogTitle, DialogContent, Typography, CircularProgress } from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { useRouter } from 'next/navigation';

interface Props {
  open: boolean;
  title: string;
  data: any[];
  endpoint: string;
  onClose: () => void;
}

export default function DrilldownModal({ open, title, data, onClose }: Props) {
  const router = useRouter();

  const getColumns = () => {
    if (title.includes('Items')) return [
      { field: 'brand_category', headerName: 'Brand/Category', flex: 1 },
      { field: 'division', headerName: 'Division', width: 100 },
      { field: 'availability_status', headerName: 'Status', width: 90 },
      { field: 'milestone', headerName: 'Milestone', width: 150 },
    ];
    if (title.includes('Actions')) return [
      { field: 'action', headerName: 'Action', flex: 1 },
      { field: 'person', headerName: 'Person', width: 100 },
      { field: 'urgency', headerName: 'Urgency', width: 80 },
      { field: 'category', headerName: 'Category', width: 120 },
    ];
    if (title.includes('Risks')) return [
      { field: 'phrase', headerName: 'Phrase', flex: 1 },
      { field: 'category', headerName: 'Category', width: 120 },
      { field: 'severity_score', headerName: 'Score', width: 60 },
    ];
    return [{ field: 'id', headerName: 'ID' }];
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent sx={{ minHeight: 200 }}>
        {data.length === 0 ? <CircularProgress /> : (
          <DataGrid rows={data} columns={getColumns()} autoHeight density="compact"
            pageSizeOptions={[10, 25, 50]} initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
            sx={{ border: 'none' }} disableRowSelectionOnClick
            onRowClick={(p) => {
              if (title.includes('Items')) router.push(`/brands/${p.row.brand_id}`);
              else if (title.includes('Actions')) router.push(`/actions/${p.row.id}`);
              onClose();
            }} />
        )}
      </DialogContent>
    </Dialog>
  );
}
