'use client';
import { Fragment, useState } from 'react';
import { Box, Button, Chip, CircularProgress, Collapse, Typography } from '@mui/material';
import { FactCheck } from '@mui/icons-material';
import api from '@/lib/api';
import { ChatCitation } from '@/types/chat';

interface VerifyRecord {
  type: string;
  id: number;
  label: string;
  found: boolean;
  fields: Record<string, unknown>;
}

export default function VerifyPanel({ citations }: { citations: ChatCitation[] }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState<VerifyRecord[] | null>(null);
  const [error, setError] = useState('');

  const toggle = async () => {
    if (open) { setOpen(false); return; }
    setOpen(true);
    if (records || loading) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.post('v1/chat/verify', {
        citations: citations.map((c) => ({ type: c.type, id: c.id, report_id: c.report_id, label: c.label })),
      });
      setRecords(res.data.records || []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ mt: 0.5 }}>
      <Button size="small" onClick={toggle} startIcon={<FactCheck sx={{ fontSize: 14 }} />}
        sx={{ textTransform: 'none', fontSize: '0.7rem', minWidth: 0, py: 0, color: 'text.secondary' }}>
        {open ? 'Hide verification' : 'Verify against database'}
      </Button>
      <Collapse in={open}>
        <Box sx={{ mt: 0.5, p: 1, border: 1, borderColor: 'divider', borderRadius: 1, bgcolor: 'action.hover' }}>
          {loading && (
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <CircularProgress size={14} />
              <Typography variant="caption">Checking the database…</Typography>
            </Box>
          )}
          {error && <Typography variant="caption" color="error">{error}</Typography>}
          {records?.map((r, i) => (
            <Box key={i} sx={{ mb: i < records.length - 1 ? 1 : 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flexWrap: 'wrap' }}>
                <Chip size="small" label={r.label} color={r.found ? 'success' : 'error'} variant="outlined"
                  sx={{ height: 18, fontSize: '0.62rem' }} />
                {!r.found && <Typography variant="caption" color="error">not found in database</Typography>}
              </Box>
              {r.found && (
                <Box sx={{ display: 'grid', gridTemplateColumns: 'auto 1fr', columnGap: 1, rowGap: 0.25, mt: 0.5 }}>
                  {Object.entries(r.fields)
                    .filter(([, v]) => v !== null && v !== undefined && v !== '')
                    .map(([k, v]) => (
                      <Fragment key={k}>
                        <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'capitalize' }}>
                          {k.replace(/_/g, ' ')}
                        </Typography>
                        <Typography variant="caption">{String(v)}</Typography>
                      </Fragment>
                    ))}
                </Box>
              )}
            </Box>
          ))}
        </Box>
      </Collapse>
    </Box>
  );
}
