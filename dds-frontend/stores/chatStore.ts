import { create } from 'zustand';
import { ChatMessage, ChatConversation, ChatCitation } from '@/types/chat';
import api from '@/lib/api';

interface ChatState {
  conversations: ChatConversation[];
  currentConversationId: number | null;
  messages: ChatMessage[];
  isOpen: boolean;
  isStreaming: boolean;
  reportId: number | null;

  setOpen: (open: boolean) => void;
  setReportContext: (reportId: number | null) => void;
  loadConversations: () => Promise<void>;
  selectConversation: (id: number) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  startNew: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversationId: null,
  messages: [],
  isOpen: false,
  isStreaming: false,
  reportId: null,

  setOpen: (open) => set({ isOpen: open }),
  setReportContext: (reportId) => set({ reportId, currentConversationId: null, messages: [] }),

  loadConversations: async () => {
    try {
      const res = await api.get('v1/chat/conversations');
      set({ conversations: res.data.conversations });
    } catch (e) {
      console.error('Failed to load conversations', e);
    }
  },

  selectConversation: async (id) => {
    try {
      const res = await api.get(`v1/chat/conversations/${id}/messages`);
      set({ currentConversationId: id, messages: res.data.messages });
    } catch (e) {
      console.error('Failed to load messages', e);
    }
  },

  sendMessage: async (content) => {
    const { currentConversationId, reportId, messages } = get();
    const userMsg: ChatMessage = {
      id: Date.now(), role: 'user', content, created_at: new Date().toISOString(),
    };
    const assistantMsg: ChatMessage = {
      id: Date.now() + 1, role: 'assistant', content: '', created_at: new Date().toISOString(),
    };
    set({ messages: [...messages, userMsg, assistantMsg], isStreaming: true });

    try {
      const url = currentConversationId
        ? `v1/chat/conversations/${currentConversationId}/send`
        : 'v1/chat/send';

      const res = await fetch(`/api/${url}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('accessToken') || ''}`,
        },
        body: JSON.stringify({ content, report_id: reportId }),
      });

      const reader = res.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const event = JSON.parse(line);
            if (event.type === 'metadata') {
              set({ currentConversationId: event.conversation_id });
            } else if (event.type === 'token') {
              const msgs = [...get().messages];
              const last = msgs[msgs.length - 1];
              if (last && last.role === 'assistant') {
                last.content += event.content;
                set({ messages: msgs });
              }
            } else if (event.type === 'done') {
              const msgs = [...get().messages];
              const last = msgs[msgs.length - 1];
              if (last && last.role === 'assistant') {
                last.id = event.message_id;
                last.citations = event.citations;
                set({ messages: msgs });
              }
              get().loadConversations();
            } else if (event.type === 'error') {
              const msgs = [...get().messages];
              const last = msgs[msgs.length - 1];
              if (last && last.role === 'assistant') {
                last.content = `Error: ${event.content}`;
                set({ messages: msgs });
              }
            }
          } catch {}
        }
      }
    } catch (e) {
      console.error('Chat stream error', e);
    } finally {
      set({ isStreaming: false });
    }
  },

  startNew: () => set({ currentConversationId: null, messages: [] }),
}));