'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  Box, Typography, IconButton, Drawer, List, ListItem, ListItemButton,
  ListItemText, Tooltip, Badge, Fab, useMediaQuery, useTheme,
} from '@mui/material';
import {
  Chat as ChatIcon, Close, Add, History, Fullscreen, FullscreenExit,
} from '@mui/icons-material';
import { useChatStore } from '@/stores/chatStore';
import ChatMessageComponent from './ChatMessage';
import ChatInput from './ChatInput';

const DEFAULT_WIDTH = 400;
const MIN_WIDTH = 320;
const WIDTH_KEY = 'chat.width';
// Matches DRAWER_WIDTH in app/(dashboard)/layout.tsx — the left menu width that
// must stay visible when the chat is maximized on desktop.
const MENU_WIDTH = 260;

function formatDateTime(value: string | null): string {
  if (!value) return '';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleString(undefined, {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
}

function pairCount(messageCount: number): number {
  // Each exchange is one user question + one assistant answer.
  return Math.ceil((messageCount || 0) / 2);
}

export default function ChatPanel() {
  const {
    isOpen, setOpen, messages, isStreaming, conversations,
    currentConversationId, reportId,
    loadConversations, selectConversation, sendMessage, startNew,
  } = useChatStore();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [width, setWidth] = useState(DEFAULT_WIDTH);
  const [maximized, setMaximized] = useState(false);

  const maxAllowed = () => window.innerWidth - (isDesktop ? MENU_WIDTH : 0);

  useEffect(() => {
    const maxW = maxAllowed();
    const saved = parseInt(window.localStorage.getItem(WIDTH_KEY) || '', 10);
    const base = Number.isNaN(saved) ? DEFAULT_WIDTH : saved;
    setWidth(Math.min(Math.max(base, MIN_WIDTH), Math.max(maxW, MIN_WIDTH)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDesktop]);

  useEffect(() => {
    const onResize = () => setWidth((w) => Math.min(w, Math.max(maxAllowed(), MIN_WIDTH)));
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDesktop]);

  useEffect(() => { if (isOpen) loadConversations(); }, [isOpen, loadConversations]);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const startResize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    const onMove = (ev: MouseEvent) => {
      const next = Math.min(Math.max(window.innerWidth - ev.clientX, MIN_WIDTH), maxAllowed());
      setMaximized(false);
      setWidth(next);
    };
    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      setWidth((w) => {
        try { window.localStorage.setItem(WIDTH_KEY, String(Math.round(w))); } catch {}
        return w;
      });
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDesktop]);

  const maximizedWidth = isDesktop ? `calc(100vw - ${MENU_WIDTH}px)` : '100vw';

  // Clicking a link inside the chat navigates to a page; shrink the panel to its
  // minimum so the destination is visible (the panel stays open).
  const minimizeForLink = (e: React.MouseEvent) => {
    const anchor = (e.target as HTMLElement | null)?.closest?.('a[href]') as HTMLAnchorElement | null;
    if (!anchor) return;
    if ((anchor.getAttribute('href') || '').startsWith('/')) {
      setMaximized(false);
      setWidth(MIN_WIDTH);
    }
  };

  return (
    <>
      <Tooltip title={reportId ? `Chat about report #${reportId}` : 'DDS Chat Assistant'}>
        <Fab color="primary" sx={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1300 }}
          onClick={() => setOpen(!isOpen)}>
          <Badge badgeContent={0} color="error">{isOpen ? <Close /> : <ChatIcon />}</Badge>
        </Fab>
      </Tooltip>

      <Drawer anchor="right" variant="persistent" open={isOpen}
        sx={{ '& .MuiDrawer-paper': { width: maximized ? maximizedWidth : width, maxWidth: '100vw', display: 'flex', flexDirection: 'column' } }}>
        {!maximized && (
          <Box onMouseDown={startResize} title="Drag to resize"
            sx={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 6, cursor: 'col-resize', zIndex: 2, '&:hover': { bgcolor: 'primary.main', opacity: 0.4 } }} />
        )}

        <Box sx={{ p: 1.5, display: 'flex', alignItems: 'center', borderBottom: 1, borderColor: 'divider' }}>
          <IconButton onClick={() => setShowHistory(!showHistory)} size="small"><History /></IconButton>
          <Typography variant="subtitle1" noWrap sx={{ flex: 1, fontWeight: 600, ml: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {reportId ? `Report #${reportId} Chat` : 'DDS Chat'}
          </Typography>
          <Tooltip title={maximized ? 'Restore' : 'Maximize'}>
            <IconButton onClick={() => setMaximized((m) => !m)} size="small" sx={{ mr: 0.5 }}>
              {maximized ? <FullscreenExit /> : <Fullscreen />}
            </IconButton>
          </Tooltip>
          <IconButton onClick={startNew} size="small" sx={{ mr: 0.5 }}><Add /></IconButton>
          <IconButton onClick={() => setOpen(false)} size="small"><Close /></IconButton>
        </Box>

        {showHistory && (
          <Box sx={{ maxHeight: 220, overflow: 'auto', borderBottom: 1, borderColor: 'divider' }}>
            <List dense>
              {conversations.map((conv) => {
                const pairs = pairCount(conv.message_count);
                return (
                  <ListItem key={conv.id} disablePadding>
                    <ListItemButton selected={conv.id === currentConversationId}
                      onClick={() => { selectConversation(conv.id); setShowHistory(false); }}>
                      <ListItemText primary={conv.title || 'New Chat'}
                        secondary={`${pairs} message${pairs === 1 ? '' : 's'} · ${formatDateTime(conv.updated_at || conv.created_at)}`}
                        primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                        secondaryTypographyProps={{ variant: 'caption', noWrap: true }} />
                    </ListItemButton>
                  </ListItem>
                );
              })}
            </List>
          </Box>
        )}

        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }} onClick={minimizeForLink}>
          {messages.length === 0 && (
            <Box sx={{ textAlign: 'center', mt: 4, color: 'text.secondary' }}>
              <ChatIcon sx={{ fontSize: 48, mb: 1, opacity: 0.3 }} />
              <Typography variant="body2">Ask anything about DDS reports, brands, tasks, or insights.</Typography>
            </Box>
          )}
          {messages.map((msg) => <ChatMessageComponent key={msg.id} message={msg} />)}
          <div ref={messagesEndRef} />
        </Box>

        <ChatInput onSend={sendMessage} disabled={isStreaming} />
      </Drawer>
    </>
  );
}
