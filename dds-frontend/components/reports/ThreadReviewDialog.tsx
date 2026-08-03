'use client';
import { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, Box,
  Checkbox, FormControlLabel, Paper, CircularProgress, Alert, Divider, Chip, IconButton, Tooltip,
} from '@mui/material';
import { Upload, Refresh, Visibility, CheckCircle, Cancel, Warning } from '@mui/icons-material';
import api from '@/lib/api';
import OriginalEmailModal from '@/components/reports/OriginalEmailModal';

interface ThreadEmail {
  subject: string;
  sender: string;
  date_str: string;
  row_count: number;
  raw_text: string;
  raw_html: string;
  valid: boolean;
}

interface Props {
  open: boolean;
  file: File | null;
  onClose: () => void;
  onDone: () => void;
}

export default function ThreadReviewDialog({ open, file, onClose, onDone }: Props) {
  const [emails, setEmails] = useState<ThreadEmail[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<string[]>([]);
  const [viewEmail, setViewEmail] = useState<{ id: number; content: string; subject: string } | null>(null);

  useEffect(() => {
    if (!open || !file) return;
    previewFile();
  }, [open, file]);

  const parseEmailDate = (subject: string): number => {
    const m1 = subject.match(/Operation DDS\s*[-–]\s*(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})/i);
    if (m1) {
      const months: Record<string, number> = { january: 1, february: 2, march: 3, april: 4, may: 5, june: 6, july: 7, august: 8, september: 9, october: 10, november: 11, december: 12 };
      return new Date(parseInt(m1[3]), months[m1[2].toLowerCase()] - 1, parseInt(m1[1])).getTime();
    }
    const m2 = subject.match(/DDS[- ](\d{2})[./](\d{2})[./](\d{4})/i);
    if (m2) return new Date(parseInt(m2[3]), parseInt(m2[2]) - 1, parseInt(m2[1])).getTime();
    return 0;
  };

  const previewFile = async () => {
    setLoading(true);
    setError(null);
    setResults([]);
    try {
      const formData = new FormData();
      formData.append('files', file as Blob);
      const res = await api.post('v1/emails/preview-upload', formData, {
        headers: { 'Content-Type': undefined as any },
      });
      const data: ThreadEmail[] = Array.isArray(res.data) ? res.data : [];
      const sorted = [...data].sort((a, b) => parseEmailDate(a.subject) - parseEmailDate(b.subject));
      setEmails(sorted);
      setSelected(new Set(sorted.map((_, i) => i)));
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ') : (detail || err.message || 'Preview failed');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const toggleEmail = (idx: number) => {
    const next = new Set(selected);
    if (next.has(idx)) next.delete(idx); else next.add(idx);
    setSelected(next);
  };

  const selectAll = () => setSelected(new Set(emails.map((_, i) => i)));
  const selectValid = () => setSelected(new Set(emails.map((e, i) => e.valid ? i : -1).filter(i => i >= 0)));
  const selectNone = () => setSelected(new Set());

  const handleProcess = async () => {
    const toProcess = emails.filter((_, i) => selected.has(i));
    if (toProcess.length === 0) return;
    setProcessing(true);
    setError(null);
    try {
      const res = await api.post('v1/emails/process-selected', {
        emails: toProcess.map((e) => ({
          subject: e.subject,
          sender: e.sender,
          date_str: e.date_str,
          raw_text: e.raw_text,
          raw_html: e.raw_html,
        })),
      });
      const msgs: string[] = Array.isArray(res.data) ? res.data.map((r: any) => r.message) : [];
      setResults(msgs);
      onDone();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Processing failed');
    } finally {
      setProcessing(false);
    }
  };

  const handleReExtract = async (idx: number) => {
    setLoading(true);
    try {
      await previewFile();
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (valid: boolean, rows: number) => {
    if (!valid) return 'error';
    if (rows >= 15) return 'success';
    return 'warning';
  };

  const getStatusLabel = (valid: boolean, rows: number) => {
    if (!valid) return 'No data';
    if (rows >= 15) return `${rows} rows`;
    return `Only ${rows} rows`;
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6">
            {loading ? 'Extracting emails...' : `${emails.length} emails found`}
          </Typography>
          <IconButton size="small" onClick={previewFile} disabled={loading}>
            <Refresh fontSize="small" />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ minHeight: 300 }}>
          {loading && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4, gap: 2 }}>
              <CircularProgress />
              <Typography color="text.secondary">Extracting emails from thread...</Typography>
            </Box>
          )}

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          {!loading && emails.length > 0 && (
            <>
              <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                <Button size="small" onClick={selectAll}>All</Button>
                <Button size="small" onClick={selectValid}>Valid only</Button>
                <Button size="small" onClick={selectNone}>None</Button>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                  {selected.size} of {emails.length} selected
                </Typography>
              </Box>

              <Paper variant="outlined" sx={{ maxHeight: 450, overflow: 'auto' }}>
                {emails.map((email, idx) => (
                  <Box key={idx} sx={{
                    display: 'flex', alignItems: 'center', py: 0.5, px: 1,
                    borderBottom: '1px solid', borderColor: 'divider',
                    bgcolor: !email.valid ? 'error.main' : 'transparent',
                    opacity: !email.valid ? 0.1 : 1,
                  }}>
                    <Checkbox
                      size="small"
                      checked={selected.has(idx)}
                      onChange={() => toggleEmail(idx)}
                    />
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="body2" fontWeight={500} noWrap>
                        {email.subject || '(no subject)'}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {email.date_str || 'no date'} · {email.sender?.substring(0, 40)}
                      </Typography>
                    </Box>
                    <Chip
                      size="small"
                      label={getStatusLabel(email.valid, email.row_count)}
                      color={getStatusColor(email.valid, email.row_count)}
                      sx={{ mr: 1 }}
                    />
                        <Tooltip title="View email">
                          <IconButton size="small" onClick={() => setViewEmail({
                            id: 0,
                            content: email.raw_html || email.raw_text,
                            subject: email.subject,
                          })}>
                        <Visibility fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                ))}
              </Paper>

              {results.length > 0 && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  {results.map((m, i) => <Typography key={i} variant="body2">{m}</Typography>)}
                </Alert>
              )}
            </>
          )}

          {!loading && emails.length === 0 && !error && (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No emails found in the uploaded file.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleProcess}
            disabled={processing || selected.size === 0 || loading}
            startIcon={processing ? <CircularProgress size={16} /> : <Upload />}
          >
            {processing ? 'Processing...' : `Process ${selected.size} Selected`}
          </Button>
        </DialogActions>
      </Dialog>

      {viewEmail && (
        <OriginalEmailModal
          open={true}
          reportId={0}
          itemCount={0}
          rawContent={{ content: viewEmail.content, subject: viewEmail.subject }}
          onClose={() => setViewEmail(null)}
        />
      )}
    </>
  );
}
