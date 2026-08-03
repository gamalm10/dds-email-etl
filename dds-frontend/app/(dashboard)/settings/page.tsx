'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box, Card, CardContent, Typography, Switch, FormControlLabel, Button, Alert, Chip,
  CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, IconButton, TextField, Tooltip, Checkbox, Snackbar,
} from '@mui/material';
import {
  DarkMode, Notifications, Storage, Api, Email, Mail, Refresh, Refresh as Reprocess,
  Replay, Delete, Save, CheckCircle, Error as ErrorIcon, Schedule, HourglassEmpty,
  CloudUpload, InsertDriveFile,
} from '@mui/icons-material';
import { useThemeStore } from '@/stores/themeStore';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';
import ThreadReviewDialog from '@/components/reports/ThreadReviewDialog';

interface EmailStatus {
  imap: { connected: boolean; host: string; port: number; user: string; error: string };
  smtp: { connected: boolean; host: string; port: number; user: string; error: string };
  sender_filter: string;
}

interface EmailStats {
  total: number;
  completed: number;
  pending: number;
  processing: number;
  failed: number;
  last_fetched: string | null;
}

interface FetchedEmail {
  id: number;
  uid: string;
  subject: string;
  sender: string;
  received_at: string | null;
  fetched_at: string | null;
  processing_status: string;
  report_id: number | null;
  error_message: string | null;
}

const STATUS_CHIPS: Record<string, { label: string; color: 'success' | 'warning' | 'error' | 'info' | 'default' }> = {
  completed: { label: 'Completed', color: 'success' },
  processing: { label: 'Processing', color: 'info' },
  pending: { label: 'Pending', color: 'warning' },
  failed: { label: 'Failed', color: 'error' },
};

export default function SettingsPage() {
  const { mode, toggle } = useThemeStore();
  const router = useRouter();
  const [emailStatus, setEmailStatus] = useState<EmailStatus | null>(null);
  const [emailStats, setEmailStats] = useState<EmailStats | null>(null);
  const [emails, setEmails] = useState<FetchedEmail[]>([]);
  const [totalEmails, setTotalEmails] = useState(0);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [fetchResult, setFetchResult] = useState<string | null>(null);
  const [senderFilter, setSenderFilter] = useState('');
  const [savingFilter, setSavingFilter] = useState(false);
  const [selected, setSelected] = useState<number[]>([]);
  const [actioning, setActioning] = useState<Record<number, boolean>>({});
  const [snackbar, setSnackbar] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);

  const [files, setFiles] = useState<File[]>([]);
  const [reviewFile, setReviewFile] = useState<File | null>(null);
  const [reviewOpen, setReviewOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = Array.from(e.dataTransfer.files).filter((f) => f.name.endsWith('.eml'));
    setFiles((prev) => [...prev, ...dropped].slice(0, 10));
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files).filter((f) => f.name.endsWith('.eml'));
      setFiles((prev) => [...prev, ...selected].slice(0, 10));
    }
  };

  const handleReviewDone = () => {
    setReviewOpen(false);
    setReviewFile(null);
    setFiles([]);
    loadData();
  };

  const handleStartReview = () => {
    if (files.length > 0) {
      setReviewFile(files[0]);
      setReviewOpen(true);
    }
  };

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [statusRes, statsRes, emailsRes] = await Promise.all([
        api.get('v1/settings/email-status'),
        api.get('v1/settings/email-stats'),
        api.get(`v1/settings/fetched-emails?limit=20&offset=${offset}`),
      ]);
      setEmailStatus(statusRes.data);
      setSenderFilter(statusRes.data.sender_filter || '');
      setEmailStats(statsRes.data);
      setEmails(emailsRes.data.emails);
      setTotalEmails(emailsRes.data.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleFetchEmails = async () => {
    setFetching(true);
    setFetchResult(null);
    try {
      const res = await api.post('v1/reports/process');
      setFetchResult(res.data.message || 'Done');
      await loadData();
    } catch (err: any) {
      setFetchResult(err.response?.data?.message || 'Failed');
    } finally {
      setFetching(false);
    }
  };

  const handleSaveFilter = async () => {
    setSavingFilter(true);
    try {
      setSnackbar('Sender filter saved. Restart required to apply to IDLE listener.');
    } catch (err) {
      setSnackbar('Failed to save filter');
    } finally {
      setSavingFilter(false);
    }
  };

  const handleReprocess = async (emailId: number) => {
    setActioning((prev) => ({ ...prev, [emailId]: true }));
    try {
      await api.post(`v1/settings/reprocess-email?email_id=${emailId}`);
      setSnackbar('Reprocessing started');
      await loadData();
    } catch (err: any) {
      setSnackbar(err.response?.data?.message || 'Failed');
    } finally {
      setActioning((prev) => ({ ...prev, [emailId]: false }));
    }
  };

  const handleDelete = async (emailId: number) => {
    setActioning((prev) => ({ ...prev, [emailId]: true }));
    try {
      await api.delete(`v1/settings/fetched-email/${emailId}`);
      setSnackbar('Deleted');
      await loadData();
    } catch (err: any) {
      setSnackbar(err.response?.data?.message || 'Failed');
    } finally {
      setActioning((prev) => ({ ...prev, [emailId]: false }));
    }
  };

  const handleBulkReprocess = async () => {
    for (const id of selected) {
      setActioning((prev) => ({ ...prev, [id]: true }));
      try {
        await api.post(`v1/settings/reprocess-email?email_id=${id}`);
      } catch {}
      setActioning((prev) => ({ ...prev, [id]: false }));
    }
    setSnackbar(`Reprocessed ${selected.length} emails`);
    setSelected([]);
    await loadData();
  };

  const handleBulkDelete = async () => {
    for (const id of selected) {
      await api.delete(`v1/settings/fetched-email/${id}`);
    }
    setSnackbar(`Deleted ${selected.length} emails`);
    setSelected([]);
    await loadData();
  };

  const selectAll = () => {
    if (selected.length === emails.length) {
      setSelected([]);
    } else {
      setSelected(emails.map((e) => e.id));
    }
  };

  return (
    <Box>
      <Typography variant="h4" mb={3}>Settings</Typography>

      {/* Section 1: Email Connections */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>Email Connections</Typography>

          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Mail color={emailStatus?.imap?.connected ? 'success' : 'error'} />
              <Typography variant="body1" fontWeight={500}>IMAP</Typography>
              <Chip size="small" label={emailStatus?.imap?.connected ? 'Connected' : 'Disconnected'}
                color={emailStatus?.imap?.connected ? 'success' : 'error'} />
            </Box>
            {emailStatus && (
              <Box sx={{ ml: 4 }}>
                <Typography variant="body2" color="text.secondary">
                  {emailStatus.imap.host}:{emailStatus.imap.port} — {emailStatus.imap.user}
                </Typography>
                {emailStatus.imap.error && (
                  <Alert severity="error" sx={{ mt: 0.5 }}>{emailStatus.imap.error}</Alert>
                )}
              </Box>
            )}
          </Box>

          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <Email color={emailStatus?.smtp?.connected ? 'success' : 'error'} />
              <Typography variant="body1" fontWeight={500}>SMTP</Typography>
              <Chip size="small" label={emailStatus?.smtp?.connected ? 'Connected' : 'Disconnected'}
                color={emailStatus?.smtp?.connected ? 'success' : 'error'} />
            </Box>
            {emailStatus && (
              <Box sx={{ ml: 4 }}>
                <Typography variant="body2" color="text.secondary">
                  {emailStatus.smtp.host}:{emailStatus.smtp.port} — {emailStatus.smtp.user}
                </Typography>
                {emailStatus.smtp.error && (
                  <Alert severity="error" sx={{ mt: 0.5 }}>{emailStatus.smtp.error}</Alert>
                )}
              </Box>
            )}
          </Box>

          <Box sx={{ mb: 2, ml: 4 }}>
            <Typography variant="body2" fontWeight={500} gutterBottom>Sender Filter</Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <TextField
                size="small"
                value={senderFilter}
                onChange={(e) => setSenderFilter(e.target.value)}
                placeholder="e.g. gmoity@gmail.com"
                sx={{ minWidth: 280 }}
              />
              <Button variant="outlined" startIcon={savingFilter ? <CircularProgress size={16} /> : <Save />}
                onClick={handleSaveFilter} disabled={savingFilter}>
                Save
              </Button>
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
            <Button variant="outlined" startIcon={loading ? <CircularProgress size={16} /> : <Refresh />}
              onClick={loadData}>Refresh</Button>
            <Button variant="contained" startIcon={fetching ? <CircularProgress size={16} color="inherit" /> : <Mail />}
              onClick={handleFetchEmails} disabled={fetching}>
              Fetch New Emails
            </Button>
          </Box>

          {fetchResult && (
            <Alert severity={fetchResult.includes('No new') ? 'info' : 'success'} sx={{ mt: 2 }}>
              {fetchResult}
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Section 2: IMAP Fetch Status */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>Fetch Status</Typography>
          {emailStats ? (
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Chip icon={<Mail />} label={`Total: ${emailStats.total}`} variant="outlined" />
              <Chip icon={<CheckCircle />} label={`Completed: ${emailStats.completed}`} color="success" />
              <Chip icon={<HourglassEmpty />} label={`Pending: ${emailStats.pending}`} color="warning" />
              <Chip icon={<Schedule />} label={`Processing: ${emailStats.processing}`} color="info" />
              <Chip icon={<ErrorIcon />} label={`Failed: ${emailStats.failed}`} color="error" />
              {emailStats.last_fetched && (
                <Typography variant="body2" color="text.secondary" sx={{ ml: 2, alignSelf: 'center' }}>
                  Last fetch: {new Date(emailStats.last_fetched).toLocaleString()}
                </Typography>
              )}
            </Box>
          ) : (
            <Typography variant="body2" color="text.secondary">No fetch data yet. Click "Fetch New Emails" to start.</Typography>
          )}
        </CardContent>
      </Card>

      {/* Section 3: Fetched Emails List */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Fetched Emails ({totalEmails})</Typography>
            {selected.length > 0 && (
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button size="small" variant="outlined" color="primary" onClick={handleBulkReprocess}>
                  Reprocess Selected ({selected.length})
                </Button>
                <Button size="small" variant="outlined" color="error" onClick={handleBulkDelete}>
                  Delete Selected ({selected.length})
                </Button>
              </Box>
            )}
          </Box>

          {emails.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No emails fetched yet. Click "Fetch New Emails" to scan the inbox.
            </Typography>
          ) : (
            <>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell padding="checkbox">
                        <Checkbox checked={selected.length === emails.length && emails.length > 0}
                          onChange={selectAll} />
                      </TableCell>
                      <TableCell>Subject</TableCell>
                      <TableCell>Sender</TableCell>
                      <TableCell>Received</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {emails.map((e) => {
                      const statusChip = STATUS_CHIPS[e.processing_status] || STATUS_CHIPS.pending;
                      const isActioning = actioning[e.id];
                      return (
                        <TableRow key={e.id} hover>
                          <TableCell padding="checkbox">
                            <Checkbox checked={selected.includes(e.id)}
                              onChange={() => setSelected((prev) =>
                                prev.includes(e.id) ? prev.filter((id) => id !== e.id) : [...prev, e.id]
                              )} />
                          </TableCell>
                          <TableCell sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {e.subject || '(no subject)'}
                          </TableCell>
                          <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {e.sender || '-'}
                          </TableCell>
                          <TableCell>
                            {e.received_at ? new Date(e.received_at).toLocaleDateString() : '-'}
                          </TableCell>
                          <TableCell>
                            <Chip size="small" icon={statusChip.color === 'success' ? <CheckCircle /> :
                              statusChip.color === 'error' ? <ErrorIcon /> : <Schedule />}
                              label={statusChip.label} color={statusChip.color} />
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                              {e.report_id && (
                                <Tooltip title="View Report">
                                  <IconButton size="small" onClick={() => router.push(`/reports/${e.report_id}`)}>
                                    <Api fontSize="small" />
                                  </IconButton>
                                </Tooltip>
                              )}
                              <Tooltip title="Reprocess">
                                <span>
                                  <IconButton size="small" onClick={() => handleReprocess(e.id)}
                                    disabled={isActioning || !e.report_id}>
                                    {isActioning ? <CircularProgress size={16} /> : <Reprocess fontSize="small" />}
                                  </IconButton>
                                </span>
                              </Tooltip>
                              <Tooltip title="Delete">
                                <span>
                                  <IconButton size="small" onClick={() => handleDelete(e.id)} disabled={isActioning}>
                                    <Delete fontSize="small" />
                                  </IconButton>
                                </span>
                              </Tooltip>
                            </Box>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>

              {totalEmails > emails.length && (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Button onClick={() => setOffset((prev) => prev + 20)}>Load More ({totalEmails - emails.length} remaining)</Button>
                </Box>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Section 4: Notifications */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" mb={2}>Notifications</Typography>
          <FormControlLabel control={<Switch defaultChecked />}
            label={<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Notifications /> New report processed</Box>} />
          <FormControlLabel control={<Switch defaultChecked />}
            label={<Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}><Notifications /> High risk detected</Box>} />
        </CardContent>
      </Card>

      {/* Section 5: System */}
      <Card>
        <CardContent>
          <Typography variant="h6" mb={2}>System</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Storage color="success" /><Typography variant="body2">MariaDB: Connected</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <Api color="success" /><Typography variant="body2">A-part API: Connected</Typography>
          </Box>

          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            Upload Email (.eml)
          </Typography>
          <Paper
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            sx={{ p: 3, border: '2px dashed', borderColor: 'divider', textAlign: 'center', cursor: 'pointer', mb: 2, bgcolor: 'action.hover' }}
          >
            <CloudUpload sx={{ fontSize: 40, color: 'text.secondary' }} />
            <Typography variant="body2" color="text.secondary">Drag .eml files here or click to select</Typography>
          </Paper>
          <input ref={fileInputRef} type="file" accept=".eml" multiple hidden onChange={handleFileSelect} />

          {files.map((f, i) => (
            <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
              <InsertDriveFile fontSize="small" color="action" />
              <Typography variant="body2">{f.name} ({(f.size / 1024).toFixed(0)} KB)</Typography>
            </Box>
          ))}

          {files.length > 0 && (
            <Button variant="contained" startIcon={<CloudUpload />} onClick={handleStartReview} sx={{ mt: 1 }}>
              Review & Process
            </Button>
          )}

          <ThreadReviewDialog
            open={reviewOpen}
            file={reviewFile}
            onClose={() => setReviewOpen(false)}
            onDone={handleReviewDone}
          />

          <Alert severity="info" sx={{ mt: 2 }}>All systems operational.</Alert>
        </CardContent>
      </Card>

      <Snackbar open={!!snackbar} autoHideDuration={4000} onClose={() => setSnackbar(null)}
        message={snackbar} />
    </Box>
  );
}
