export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: ChatCitation[];
  created_at: string;
}

export interface ChatCitation {
  type: string;
  id: number;
  report_id: number;
  label: string;
}

export interface ChatConversation {
  id: number;
  report_id: number | null;
  title: string | null;
  created_at: string;
  updated_at: string | null;
  message_count: number;
}

export type ChatStreamEvent =
  | { type: 'metadata'; conversation_id: number }
  | { type: 'token'; content: string }
  | { type: 'done'; message_id: number; citations: ChatCitation[] }
  | { type: 'error'; content: string };