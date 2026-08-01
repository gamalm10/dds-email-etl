'use client';
import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Box, Card, CardContent, Typography, Button, List, ListItem, ListItemIcon, ListItemText,
  Chip, CircularProgress, Alert, Paper,
} from '@mui/material';
import { CloudUpload, InsertDriveFile, CheckCircle, Error as ErrorIcon, Assessment } from '@mui/icons-material';
import api from '@/lib/api';

export default function UploadPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [dragOver, setDragOver] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = Array.from(e.dataTransfer.files).filter((f) => f.name.endsWith('.eml'));
    setFiles((prev) => [...prev, ...dropped].slice(0, 10));
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selected = Array.from(e.target.files).filter((f) => f.name.endsWith('.eml'));
      setFiles((prev) => [...prev, ...selected].slice(0, 10));
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setResults([]);
    try {
      const formData = new FormData();
      files.forEach((f) => formData.append('files', f));
      const res = await api.post('v1/reports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
      });
      setResults(res.data);
    } catch (err: any) {
      setResults([{ success: false, message: err.message || 'Upload failed' }]);
    } finally {
      setUploading(false);
    }
  };

  const clearAll = () => { setFiles([]); setResults([]); };

  return (
    <Box>
      <Typography variant="h4" mb={3}>Upload Email</Typography>

      <Paper
        onDrop={handleDrop}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        sx={{
          p: 6, mb: 3, textAlign: 'center', border: '2px dashed', borderColor: dragOver ? 'primary.main' : 'divider',
          bgcolor: dragOver ? 'action.hover' : 'background.paper', borderRadius: 3, cursor: 'pointer', transition: 'all 0.2s',
        }}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <CloudUpload sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" mb={1}>Drag & drop .eml files here</Typography>
        <Typography variant="body2" color="text.secondary" mb={2}>or click to browse (max 10 files)</Typography>
        <input id="file-input" type="file" multiple accept=".eml" hidden onChange={handleFileSelect} />
        <Button variant="outlined" component="span">Select Files</Button>
      </Paper>

      {files.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" mb={2}>Selected Files ({files.length})</Typography>
            <List dense>
              {files.map((f, i) => (
                <ListItem key={i}>
                  <ListItemIcon><InsertDriveFile /></ListItemIcon>
                  <ListItemText primary={f.name} secondary={`${(f.size / 1024).toFixed(1)} KB`} />
                </ListItem>
              ))}
            </List>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Button variant="contained" onClick={handleUpload} disabled={uploading} startIcon={uploading ? <CircularProgress size={20} /> : <CloudUpload />}>
                {uploading ? 'Processing...' : `Upload & Process (${files.length})`}
              </Button>
              <Button variant="outlined" onClick={clearAll} disabled={uploading}>Clear</Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {results.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" mb={2}>Results</Typography>
            {results.map((r, i) => (
              <Alert key={i} severity={r.success ? 'success' : 'error'} sx={{ mb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                  <Typography variant="body2">{r.message}</Typography>
                  {r.success && <Chip label={`Report #${r.report_id}`} size="small" onClick={() => router.push(`/reports/${r.report_id}`)} sx={{ cursor: 'pointer' }} />}
                  {r.items_extracted > 0 && <Chip label={`${r.items_extracted} items`} size="small" />}
                  {r.tasks_extracted > 0 && <Chip label={`${r.tasks_extracted} tasks`} size="small" />}
                  {r.insights_generated > 0 && <Chip label={`${r.insights_generated} insights`} size="small" />}
                </Box>
              </Alert>
            ))}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
