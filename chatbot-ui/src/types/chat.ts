export type Role = 'user' | 'assistant';

export interface MessageSource {
  engine: 'green' | 'yellow' | 'red' | 'system';
  domain: string;
  intent: string;
  score: number;
  content: string;
  source: string;
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  createdAt: string;
  sources?: MessageSource[];
}

export interface ChatApiResponse {
  conversation_id: string;
  message: {
    id: string;
    role: 'assistant';
    content: string;
    created_at: string;
  };
  sources: MessageSource[];
  warnings: string[];
}
