'use client';
import { useState } from 'react';
import {
  Box, Button, Chip, CircularProgress, Collapse, Paper, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Tooltip, Typography,
} from '@mui/material';
import { FactCheck } from '@mui/icons-material';
import api from '@/lib/api';
import { ChatCitation } from '@/types/chat';
import { colorizeStatusChildren } from '@/lib/statusColors';

interface VerifyRecord {
  type: string;
  id: number;
  label: string;
  found: boolean;
  fields: Record<string, unknown>;
}

// Preferred column order for the combined table.
const PREFERRED_ORDER = [
  'brand', 'division', 'availability', 'vendor', 'milestone', 'etd', 'eta', 'ready_for_sale',
  'quantity', 'financial', 'comments', 'report_id', 'report_date', 'report_subject',
  'type', 'severity', 'description', 'impact', 'recommendation', 'risk_tags',
  'assignee', 'deadline', 'status', 'priority', 'category', 'overdue', 'blocked', 'occurrences',
];

// Fields whose values can be long — ellipsized with a hover tooltip.
const LONG_FIELDS = new Set(['comments', 'description', 'impact', 'recommendation', 'risk_tags']);

const humanize = (k: string) => k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

function cellValue(v: unknown): string {
  if (v === null || v === undefined || v === '') return '—';
  if (typeof v === 'boolean') return v ? 'Yes' : 'No';
  return String(v);
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

  const found = records?.filter((r) => r.found) ?? [];
  const present = new Set<string>();
  found.forEach((r) => Object.keys(r.fields).forEach((k) => present.add(k)));
  const columns = [
    ...PREFERRED_ORDER.filter((k) => present.has(k)),
    ...[...present].filter((k) => !PREFERRED_ORDER.includes(k)).sort(),
  ];

  return (
    <Box sx={{ mt: 0.5 }}>
      <Button size="small" onClick={toggle} startIcon={<FactCheck sx={{ fontSize: 14 }} />}
        sx={{ textTransform: 'none', fontSize: '0.7rem', minWidth: 0, py: 0, color: 'text.secondary' }}>
        {open ? 'Hide verification' : 'Verify against database'}
      </Button>

      <Collapse in={open}>
        <Box sx={{ mt: 0.5 }}>
          {loading && (
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', p: 1 }}>
              <CircularProgress size={14} />
              <Typography variant="caption">Checking the database…</Typography>
            </Box>
          )}
          {error && <Typography variant="caption" color="error" sx={{ display: 'block', p: 1 }}>{error}</Typography>}

          {records && records.length > 0 && (
            <>
              <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5, fontWeight: 700, mb: 0.5, color: 'text.secondary' }}>
                <FactCheck sx={{ fontSize: 14 }} /> Verified against database
              </Typography>
              <TableContainer component={Paper} variant="outlined" sx={{ width: '100%', overflowX: 'auto', borderRadius: 1 }}>
                <Table size="small" sx={{
                  '& th, & td': { fontSize: '0.7rem', py: 0.4, px: 0.75, whiteSpace: 'nowrap', verticalAlign: 'top', borderColor: 'divider' },
                  '& tbody tr:nth-of-type(odd)': { bgcolor: 'action.hover' },
                }}>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 700 }}>Record</TableCell>
                      {columns.map((c) => <TableCell key={c} sx={{ fontWeight: 700 }}>{humanize(c)}</TableCell>)}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {records.map((r, i) => (
                      <TableRow key={i}>
                        <TableCell>
                          <Chip size="small" label={r.label} color={r.found ? 'success' : 'error'} variant="outlined"
                            sx={{ height: 18, fontSize: '0.62rem' }} />
                        </TableCell>
                        {r.found ? (
                          columns.map((c) => {
                            const val = cellValue(r.fields[c]);
                            const long = LONG_FIELDS.has(c);
                            return (
                              <TableCell key={c} sx={long ? { maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis' } : undefined}>
                                {long && val !== '—'
                                  ? <Tooltip title={val}><span>{colorizeStatusChildren(val)}</span></Tooltip>
                                  : colorizeStatusChildren(val)}
                              </TableCell>
                            );
                          })
                        ) : (
                          <TableCell colSpan={Math.max(columns.length, 1)} sx={{ color: 'error.main' }}>
                            not found in database
                          </TableCell>
                        )}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </Box>
      </Collapse>
    </Box>
  );
}
