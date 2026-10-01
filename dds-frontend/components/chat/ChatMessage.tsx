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
          href={
            c.type === 'report_item'
              ? `/reports/${c.report_id}?hl=item-${c.id}`
              : c.type === 'task'
                ? `/tasks/${c.id}?hl=task-${c.id}`
                : `/insights/${c.id}?hl=insight-${c.id}`
          }
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
      </Box>
    </Box>
  );
}
