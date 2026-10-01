'use client';
import { Box, Typography, Chip, CircularProgress } from '@mui/material';
import { SmartToy, Person } from '@mui/icons-material';
import { ChatMessage as ChatMsg, ChatCitation } from '@/types/chat';

const THINKING_PLACEHOLDER = 'Analysing your question…';

function citationHref(c: ChatCitation): string | null {
  if (c.type === 'report_item') return `/reports/${c.report_id}?hl=item-${c.id}`;
  if (c.type === 'task') return `/tasks/${c.id}?hl=task-${c.id}`;
  if (c.type === 'insight') return `/insights/${c.id}?hl=insight-${c.id}`;
  return null;
}

function formatTimestamp(value: string): string {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  const sameDay = d.toDateString() === new Date().toDateString();
  return sameDay
    ? d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })
    : d.toLocaleString(undefined, { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

function CitationChips({ citations }: { citations: ChatCitation[] }) {
  const linked = citations.filter((c) => citationHref(c) !== null);
  if (linked.length === 0) return null;
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
      {linked.map((c, i) => (
        <Chip key={i} label={c.label} size="small" component="a" href={citationHref(c) || undefined}
          clickable sx={{ fontSize: '0.7rem', height: 20 }} />
      ))}
    </Box>
  );
}

export default function ChatMessage({ message }: { message: ChatMsg }) {
  const isUser = message.role === 'user';
  const isPending = !isUser && message.content === THINKING_PLACEHOLDER;
  const timestamp = formatTimestamp(message.created_at);

  return (
    <Box sx={{ display: 'flex', gap: 1, mb: 2, flexDirection: isUser ? 'row-reverse' : 'row', alignItems: 'flex-start' }}>
      <Box sx={{
        width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
        bgcolor: isUser ? 'primary.main' : 'background.paper', color: isUser ? 'primary.contrastText' : 'text.primary', flexShrink: 0,
        border: isUser ? 'none' : 1,
        borderColor: 'divider',
      }}>
        {isUser ? <Person sx={{ fontSize: 18 }} /> : <SmartToy sx={{ fontSize: 18 }} />}
      </Box>
      <Box sx={{
        width: 'fit-content',
        maxWidth: '80%',
        minWidth: 0,
        p: 1.5,
        borderRadius: 2,
        // Theme-aware colours. Hardcoding grey.100 left white text on a white
        // bubble in dark mode, where text.primary is white.
        bgcolor: isUser ? 'primary.main' : 'background.paper',
        color: isUser ? 'primary.contrastText' : 'text.primary',
        border: isUser ? 'none' : 1,
        borderColor: 'divider',
        overflowWrap: 'anywhere',
        wordBreak: 'break-word',
      }}>
        {isPending ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
            <CircularProgress size={14} />
            <Typography variant="body2">{THINKING_PLACEHOLDER}</Typography>
          </Box>
        ) : (
          <Typography variant="body2" component="div" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
            {message.content}
          </Typography>
        )}
        {!isUser && message.citations && message.citations.length > 0 && (
          <CitationChips citations={message.citations} />
        )}
        {timestamp && (
          <Typography variant="caption" sx={{
            display: 'block', mt: 0.5, fontSize: '0.65rem', opacity: 0.7,
            color: isUser ? 'primary.contrastText' : 'text.secondary',
            textAlign: isUser ? 'right' : 'left',
          }}>
            {timestamp}
          </Typography>
        )}
      </Box>
    </Box>
  );
}
