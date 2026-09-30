'use client';
import { Box, Typography, Chip, CircularProgress } from '@mui/material';
import { SmartToy, Person } from '@mui/icons-material';
import { ChatMessage as ChatMsg, ChatCitation } from '@/types/chat';

const THINKING_PLACEHOLDER = 'Analysing your question…';

function CitationChips({ citations }: { citations: ChatCitation[] }) {
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
      {citations.map((c, i) => (
        <Chip key={i} label={c.label} size="small" component="a"
          href={c.type === 'report_item' ? `/reports/${c.report_id}` : `/${c.type === 'task' ? 'tasks' : 'insights'}/${c.id}`}
          clickable sx={{ fontSize: '0.7rem', height: 20 }} />
      ))}
    </Box>
  );
}

export default function ChatMessage({ message }: { message: ChatMsg }) {
  const isUser = message.role === 'user';
  const isPending = !isUser && message.content === THINKING_PLACEHOLDER;

  return (
    <Box sx={{ display: 'flex', gap: 1, mb: 2, flexDirection: isUser ? 'row-reverse' : 'row', alignItems: 'flex-start' }}>
      <Box sx={{
        width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
        bgcolor: isUser ? 'primary.main' : 'grey.300', color: isUser ? 'white' : 'text.primary', flexShrink: 0,
      }}>
        {isUser ? <Person sx={{ fontSize: 18 }} /> : <SmartToy sx={{ fontSize: 18 }} />}
      </Box>
      <Box sx={{
        maxWidth: '80%', p: 1.5, borderRadius: 2,
        bgcolor: isUser ? 'primary.main' : 'grey.100', color: isUser ? 'white' : 'text.primary',
      }}>
        {isPending ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
            <CircularProgress size={14} />
            <Typography variant="body2">{THINKING_PLACEHOLDER}</Typography>
          </Box>
        ) : (
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
            {message.content}
          </Typography>
        )}
        {!isUser && message.citations && message.citations.length > 0 && (
          <CitationChips citations={message.citations} />
        )}
      </Box>
    </Box>
  );
}
