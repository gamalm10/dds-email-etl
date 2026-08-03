'use client';
import { useEffect, useState } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button, Typography, CircularProgress, Box, Alert,
  IconButton, Tooltip, Snackbar, Checkbox, FormControlLabel, Divider, Paper,
} from '@mui/material';
import { ContentCopy, Download, Upload, Close } from '@mui/icons-material';
import api from '@/lib/api';

interface Props {
  open: boolean;
  reportId: number;
  itemCount: number;
  rawContent?: { content: string; subject: string; sender?: string; date?: string } | null;
  onClose: () => void;
  onReuploadDone?: () => void;
}

interface RawEmail {
  content: string;
  content_type: string;
  subject: string;
  sender: string;
  date: string | null;
}

interface ThreadEmail {
  subject: string;
  sender: string;
  date_str: string;
  row_count: number;
  raw_text: string;
}

export default function OriginalEmailModal({ open, reportId, itemCount, rawContent, onClose, onReuploadDone }: Props) {
  const [data, setData] = useState<RawEmail | null>(null);
  const [loading, setLoading] = useState(false);
  const [reprocessing, setReprocessing] = useState(false);
  const [reuploading, setReuploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState<string | null>(null);
  const [threadEmails, setThreadEmails] = useState<ThreadEmail[]>([]);
  const [selectedThread, setSelectedThread] = useState<Set<number>>(new Set());
  const [showThreadPicker, setShowThreadPicker] = useState(false);
  const [copied, setCopied] = useState(false);

  const fetchRaw = () => {
    if (!open) return;
    if (rawContent) {
      setLoading(false);
      setError(null);
      const isHtml = rawContent.content && (rawContent.content.includes('<table') || rawContent.content.includes('<html') || rawContent.content.includes('<body'));
      setData({ content: rawContent.content, content_type: isHtml ? 'html' : 'text', subject: rawContent.subject, sender: rawContent.sender || '', date: rawContent.date || null });
      return;
    }
    if (!reportId) return;
    setLoading(true);
    setError(null);
    setData(null);
    setShowThreadPicker(false);
    setThreadEmails([]);
    api.get(`v1/reports/${reportId}/raw`)
      .then(({ data }) => setData(data))
      .catch((err) => setError(err.message || 'Failed to load'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchRaw(); }, [open, reportId]);

  const handleCopy = async () => {
    if (!data?.content) return;
    try {
      await navigator.clipboard.writeText(data.content);
      setCopied(true);
      setSnackbar('Copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setSnackbar('Copy failed');
    }
  };

  const handleDownload = () => {
    if (!data?.content) return;
    const safeSubject = (data.subject || `report-${reportId}`).replace(/[<>:"/\\|?*]/g, '-').substring(0, 80);
    const blob = new Blob([data.content], { type: 'message/rfc822' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${safeSubject}.eml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setSnackbar('Download started');
  };

  const handleReuploadStart = async () => {
    setReuploading(true);
    setError(null);
    try {
      const previewRes = await api.post('v1/emails/preview-thread', { content: data?.content });
      const emails: ThreadEmail[] = Array.isArray(previewRes.data) ? previewRes.data : [];
      if (emails.length > 1) {
        setThreadEmails(emails);
        setSelectedThread(new Set(emails.map((_, i) => i)));
        setShowThreadPicker(true);
      } else if (emails.length === 1) {
        await uploadSingle(data?.content || '', data?.subject || '');
      } else {
        setError('No emails found in content');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Preview failed');
    } finally {
      setReuploading(false);
    }
  };

  const uploadSelected = async () => {
    const selected = threadEmails.filter((_, i) => selectedThread.has(i));
    if (selected.length === 0) return;
    setReuploading(true);
    let done = 0;
    let failed = 0;
    for (const email of selected) {
      try {
        await uploadSingle(email.raw_text, email.subject);
        done++;
      } catch { failed++; }
    }
    setReuploading(false);
    setShowThreadPicker(false);
    setSnackbar(`Uploaded ${done}${failed ? `, ${failed} failed` : ''} email(s)`);
    onReuploadDone?.();
  };

  const uploadSingle = async (content: string, subject: string) => {
    const safeSubject = subject.replace(/[<>:"/\\|?*]/g, '-').substring(0, 80) || `report-${reportId}`;
    const blob = new Blob([content], { type: 'message/rfc822' });
    const file = new File([blob], `${safeSubject}.eml`, { type: 'message/rfc822' });
    const formData = new FormData();
    formData.append('files', file);
    await api.post('v1/reports/upload', formData);
  };

  const handleReprocess = async () => {
    setReprocessing(true);
    setError(null);
    try {
      await api.post(`v1/reports/${reportId}/reprocess`);
      fetchRaw();
      setSnackbar('Report reprocessed');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Reprocess failed');
    } finally {
      setReprocessing(false);
    }
  };

  const toggleThread = (idx: number) => {
    const next = new Set(selectedThread);
    if (next.has(idx)) next.delete(idx); else next.add(idx);
    setSelectedThread(next);
  };

  const selectAll = () => setSelectedThread(new Set(threadEmails.map((_, i) => i)));
  const selectNone = () => setSelectedThread(new Set());

  const parseHeaders = () => {
    if (!data?.content) return { from: '', date: '', to: '', subject: '', body: '' };
    const content = data.content;
    const from = content.match(/^From:\s*(.+)/m)?.[1] || '';
    const date = content.match(/^Date:\s*(.+)/m)?.[1] || '';
    const to = content.match(/^To:\s*(.+)/m)?.[1] || '';
    const subject = content.match(/^Subject:\s*(.+)/m)?.[1] || '';
    const bodyStart = content.indexOf('\r\n\r\n');
    const body = bodyStart >= 0 ? content.substring(bodyStart + 4).trim() : '';
    return { from, date, to, subject: subject || data.subject, body };
  };

  const wrapHtml = (content: string) => {
    if (/<html/i.test(content)) return content;
    return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
      body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 13px; margin: 8px; }
      table { border-collapse: collapse; margin: 8px 0; }
      td, th { border: 1px solid #ccc; padding: 4px 8px; vertical-align: top; }
      p { margin: 4px 0; }
    </style></head><body>${content}</body></html>`;
  };

  const headers = parseHeaders();
  const isEmpty = data && !data.content && !data.content_type;
  const showEmptyMessage = isEmpty && itemCount > 0;

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6">Original Email</Typography>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Tooltip title="Copy to clipboard">
              <IconButton size="small" disabled={!data?.content} onClick={handleCopy} color={copied ? 'success' : 'default'}>
                <ContentCopy fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Download .eml">
              <IconButton size="small" disabled={!data?.content} onClick={handleDownload}>
                <Download fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Re-upload">
              <IconButton size="small" disabled={!data?.content || reuploading} onClick={handleReuploadStart} color="primary">
                <Upload fontSize="small" />
              </IconButton>
            </Tooltip>
            <IconButton size="small" onClick={onClose}><Close fontSize="small" /></IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ minHeight: 300 }}>
          {loading && <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}><CircularProgress /></Box>}
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          {reprocessing && <Alert severity="info" sx={{ mb: 2 }}>Reprocessing... This may take a moment.</Alert>}
          {reuploading && <Alert severity="info" sx={{ mb: 2 }}>Uploading emails...</Alert>}

          {showEmptyMessage && (
            <Alert severity="warning" sx={{ mb: 2 }} action={
              <Button color="inherit" size="small" onClick={handleReprocess} disabled={reprocessing}>
                {reprocessing ? 'Processing...' : 'Reprocess'}
              </Button>
            }>
              Raw email content was not stored at import time.
            </Alert>
          )}

          {showThreadPicker && (
            <Box sx={{ mb: 2 }}>
              <Alert severity="info" sx={{ mb: 1 }}>
                This email contains {threadEmails.length} emails. Select which to upload:
              </Alert>
              <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                <Button size="small" onClick={selectAll}>Select All</Button>
                <Button size="small" onClick={selectNone}>Deselect All</Button>
              </Box>
              <Paper variant="outlined" sx={{ maxHeight: 300, overflow: 'auto', mb: 1 }}>
                {threadEmails.map((te, i) => (
                  <Box key={i} sx={{ display: 'flex', alignItems: 'center', px: 1, py: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                    <FormControlLabel
                      control={<Checkbox size="small" checked={selectedThread.has(i)} onChange={() => toggleThread(i)} />}
                      label={
                        <Box>
                          <Typography variant="body2" fontWeight={500}>{te.subject || '(no subject)'}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {te.date_str || 'no date'} · {te.row_count} rows · {te.sender?.substring(0, 40)}
                          </Typography>
                        </Box>
                      }
                      sx={{ flex: 1, mr: 0 }}
                    />
                  </Box>
                ))}
              </Paper>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button variant="contained" size="small" onClick={uploadSelected} disabled={reuploading || selectedThread.size === 0}>
                  Upload {selectedThread.size} selected
                </Button>
                <Button size="small" onClick={() => setShowThreadPicker(false)}>Cancel</Button>
              </Box>
            </Box>
          )}

          {data && data.content && !showThreadPicker && (
            <Box>
              {headers.from && data.content_type !== 'html' && (
                <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
                  {headers.from && <Typography variant="body2"><strong>From:</strong> {headers.from}</Typography>}
                  {headers.date && <Typography variant="body2"><strong>Date:</strong> {headers.date}</Typography>}
                  {headers.to && <Typography variant="body2"><strong>To:</strong> {headers.to}</Typography>}
                  {headers.subject && <Typography variant="body2"><strong>Subject:</strong> {headers.subject}</Typography>}
                </Paper>
              )}
              {data.content_type === 'html' ? (
                <iframe
                  srcDoc={wrapHtml(data.content)}
                  style={{ width: '100%', minHeight: 500, border: '1px solid #ddd', borderRadius: 4 }}
                  title="Original email content"
                />
              ) : (
                <Box component="pre" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: 13, p: 2, bgcolor: 'grey.50', borderRadius: 1, maxHeight: 500, overflow: 'auto' }}>
                  {headers.body || data.content}
                </Box>
              )}
            </Box>
          )}

          {!loading && !error && !data?.content && !showEmptyMessage && !showThreadPicker && (
            <Typography color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
              No content available.
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          {!showThreadPicker && data?.content && (
            <Button onClick={handleReuploadStart} disabled={reuploading} startIcon={reuploading ? <CircularProgress size={16} /> : <Upload />} color="primary">
              Re-upload as New Report
            </Button>
          )}
          <Button onClick={onClose}>Close</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar(null)} anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        message={snackbar || ''} />
    </>
  );
}
