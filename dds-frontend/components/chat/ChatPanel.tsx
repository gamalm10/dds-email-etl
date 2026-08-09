'use client';
import { useEffect, useRef, useState } from 'react';
import {
  Box, Typography, IconButton, Drawer, List, ListItem, ListItemButton,
  ListItemText, Tooltip, Badge, Fab,
} from '@mui/material';
import { Chat as ChatIcon, Close, Add, History } from '@mui/icons-material';
import { useChatStore } from '@/stores/chatStore';
import ChatMessageComponent from './ChatMessage';
import ChatInput from './ChatInput';

export default function ChatPanel() {
  const {
    isOpen, setOpen, messages, isStreaming, conversations,
    currentConversationId, reportId,
    loadConversations, selectConversation, sendMessage, startNew,
  } = useChatStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => { if (isOpen) loadConversations(); }, [isOpen, loadConversations]);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  return (
    <>
      <Tooltip title={reportId ? `Chat about report #${reportId}` : 'DDS Chat Assistant'}>
        <Fab color="primary" sx={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1300 }}
          onClick={() => setOpen(!isOpen)}>
          <Badge badgeContent={0} color="error">{isOpen ? <Close /> : <ChatIcon />}</Badge>
        </Fab>
      </Tooltip>

      <Drawer anchor="right" open={isOpen} onClose={() => setOpen(false)}
        sx={{ '& .MuiDrawer-paper': { width: 400, display: 'flex', flexDirection: 'column' } }}>
        <Box sx={{ p: 1.5, display: 'flex', alignItems: 'center', borderBottom: 1, borderColor: 'divider' }}>
          <IconButton onClick={() => setShowHistory(!showHistory)} size="small"><History /></IconButton>
          <Typography variant="subtitle1" sx={{ flex: 1, fontWeight: 600, ml: 1 }}>
            {reportId ? `Report #${reportId} Chat` : 'DDS Chat'}
          </Typography>
          <IconButton onClick={startNew} size="small" sx={{ mr: 1 }}><Add /></IconButton>
          <IconButton onClick={() => setOpen(false)} size="small"><Close /></IconButton>
        </Box>

        {showHistory && (
          <Box sx={{ maxHeight: 200, overflow: 'auto', borderBottom: 1, borderColor: 'divider' }}>
            <List dense>
              {conversations.map((conv) => (
                <ListItem key={conv.id} disablePadding>
                  <ListItemButton selected={conv.id === currentConversationId}
                    onClick={() => { selectConversation(conv.id); setShowHistory(false); }}>
                    <ListItemText primary={conv.title || 'New Chat'}
                      secondary={`${conv.message_count} messages`}
                      primaryTypographyProps={{ variant: 'body2', noWrap: true }} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
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
