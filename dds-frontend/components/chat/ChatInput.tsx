'use client';
import { useState } from 'react';
import { Box, TextField, IconButton, CircularProgress } from '@mui/material';
import { Send } from '@mui/icons-material';

export default function ChatInput({ onSend, disabled }: { onSend: (msg: string) => void; disabled: boolean }) {
  const [value, setValue] = useState('');
  const handleSend = () => { if (value.trim() && !disabled) { onSend(value.trim()); setValue(''); } };

  return (
    <Box sx={{ display: 'flex', gap: 1, p: 1.5, borderTop: 1, borderColor: 'divider' }}>
      <TextField fullWidth size="small" placeholder="Ask about reports, brands, tasks..."
        value={value} onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
        disabled={disabled} multiline maxRows={4} />
      <IconButton onClick={handleSend} disabled={!value.trim() || disabled} color="primary">
        {disabled ? <CircularProgress size={20} /> : <Send />}
      </IconButton>
    </Box>
  );
}
