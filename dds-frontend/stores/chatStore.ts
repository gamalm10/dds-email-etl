import { create } from 'zustand';
import { ChatMessage, ChatConversation, ChatCitation } from '@/types/chat';
import api from '@/lib/api';
import { apiFetch } from '@/lib/apiFetch';

const THINKING_PLACEHOLDER = 'Analysing your question…';
const NO_RESPONSE = 'No response received. Please try again.';

interface ChatState {
  conversations: ChatConversation[];
  currentConversationId: number | null;
  messages: ChatMessage[];
  isOpen: boolean;
  isStreaming: boolean;
  isThinking: boolean;
  reportId: number | null;

  setOpen: (open: boolean) => void;
  setReportContext: (reportId: number | null) => void;
  loadConversations: () => Promise<void>;
  selectConversation: (id: number) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  startNew: () => void;
}

let inFlight: AbortController | null = null;

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversationId: null,
  messages: [],
  isOpen: false,
  isStreaming: false,
  isThinking: false,
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

    inFlight?.abort();
    const controller = new AbortController();
    inFlight = controller;

    const userMsg: ChatMessage = {
      id: Date.now(), role: 'user', content, created_at: new Date().toISOString(),
    };
    const replyId = Date.now() + 1;
    const assistantMsg: ChatMessage = {
      id: replyId, role: 'assistant', content: THINKING_PLACEHOLDER,
      created_at: new Date().toISOString(),
    };
    set({ messages: [...messages, userMsg, assistantMsg], isStreaming: true, isThinking: true });

    const patchReply = (fn: (m: ChatMessage) => ChatMessage) => {
      const msgs = [...get().messages];
      const idx = msgs.findIndex((m) => m.id === replyId);
      if (idx >= 0) {
        msgs[idx] = fn(msgs[idx]);
        set({ messages: msgs });
      }
    };

    try {
      const url = currentConversationId
        ? `v1/chat/conversations/${currentConversationId}/send`
        : 'v1/chat/send';

      const res = await apiFetch(`/api/${url}`, {
        method: 'POST',
        body: JSON.stringify({ content, report_id: reportId }),
        signal: controller.signal,
      });

      if (!res.ok) {
        const detail = await res.text().catch(() => '');
        throw new Error(detail.slice(0, 200) || `Request failed (${res.status})`);
      }

      const reader = res.body?.getReader();
      if (!reader) {
        throw new Error('Streaming is not supported by this browser');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let gotTokens = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          let event: any;
          try {
            event = JSON.parse(line);
          } catch {
            continue;
          }

          if (event.type === 'metadata') {
            set({ currentConversationId: event.conversation_id });
          } else if (event.type === 'thinking') {
            set({ isThinking: true });
          } else if (event.type === 'token') {
            if (!gotTokens) {
              gotTokens = true;
              set({ isThinking: false });
              patchReply((m) => ({ ...m, content: '' }));
            }
            patchReply((m) => ({ ...m, content: m.content + event.content }));
          } else if (event.type === 'done') {
            patchReply((m) => ({ ...m, id: event.message_id, citations: event.citations }));
            set({ isThinking: false });
            get().loadConversations();
          } else if (event.type === 'error') {
            patchReply((m) => ({ ...m, content: `Error: ${event.content}` }));
            set({ isThinking: false });
          }
        }
      }

      // The stream ended without a done event. Surface it instead of leaving a
      // placeholder bubble behind forever.
      patchReply((m) => (m.content.trim() && m.content !== THINKING_PLACEHOLDER ? m : { ...m, content: NO_RESPONSE }));
    } catch (e: any) {
      if (e?.name === 'AbortError') {
        patchReply((m) => ({ ...m, content: 'Request cancelled.' }));
      } else {
        console.error('Chat stream error', e);
        patchReply((m) => ({ ...m, content: `Error: ${e?.message || 'chat failed'}` }));
      }
    } finally {
      if (inFlight === controller) inFlight = null;
      set({ isStreaming: false, isThinking: false });
    }
  },

  startNew: () => {
    inFlight?.abort();
    set({ currentConversationId: null, messages: [] });
  },
}));
