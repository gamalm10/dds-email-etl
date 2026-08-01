'use client';
import { useEffect, useState } from 'react';
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, CircularProgress, Box } from '@mui/material';
import api from '@/lib/api';

interface Props {
  open: boolean;
  reportId: number;
  onClose: () => void;
}

interface RawEmail {
  content: string;
  content_type: string;
  subject: string;
  sender: string;
  date: string | null;
}

export default function OriginalEmailModal({ open, reportId, onClose }: Props) {
  const [data, setData] = useState<RawEmail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open || !reportId) return;
    setLoading(true);
    setError(null);
    setData(null);
    api.get(`v1/reports/${reportId}/raw`)
      .then(({ data }) => setData(data))
      .catch((err) => setError(err.message || 'Failed to load'))
      .finally(() => setLoading(false));
  }, [open, reportId]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>Original Email</DialogTitle>
      <DialogContent sx={{ minHeight: 300 }}>
        {loading && <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress /></Box>}
        {error && <Typography color="error">{error}</Typography>}
        {data && (
          <Box>
            <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="body2"><strong>Subject:</strong> {data.subject}</Typography>
              <Typography variant="body2"><strong>From:</strong> {data.sender}</Typography>
              {data.date && <Typography variant="body2"><strong>Date:</strong> {new Date(data.date).toLocaleString()}</Typography>}
            </Box>
            {data.content_type === 'html' ? (
              <iframe
                srcDoc={data.content}
                style={{ width: '100%', minHeight: 500, border: '1px solid #ddd', borderRadius: 4 }}
                title="Original email content"
              />
            ) : (
              <Box component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: 13, p: 2, bgcolor: 'grey.50', borderRadius: 1, maxHeight: 500, overflow: 'auto' }}>
                {data.content}
              </Box>
            )}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
