import { useCallback, useEffect, useRef, useState } from 'react';

import { sendMessage } from '@/services/chatService';
import type { Message, Role } from '@/types/chat';
import { INITIAL_ASSISTANT_MESSAGE } from '@/constants/config';

function makeMessage(role: Role, content: string): Message {
  return {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
    role,
    content,
    createdAt: new Date().toISOString(),
  };
}

const welcomeMessage = (): Message => makeMessage('assistant', INITIAL_ASSISTANT_MESSAGE);

export function useChat() {
  const [messages, setMessages] = useState<Message[]>(() => [welcomeMessage()]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const inFlight = useRef(false);
  const conversationId = useRef<string | null>(null);
  const activeRequest = useRef<AbortController | null>(null);
  const requestVersion = useRef(0);

  useEffect(() => {
    return () => activeRequest.current?.abort();
  }, []);

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || inFlight.current) return;

    inFlight.current = true;
    setError(null);
    setIsLoading(true);

    const userMsg = makeMessage('user', trimmed);
    setMessages((prev) => [...prev, userMsg]);
    const version = ++requestVersion.current;
    const controller = new AbortController();
    activeRequest.current = controller;

    try {
      const response = await sendMessage(trimmed, conversationId.current, controller.signal);
      if (version !== requestVersion.current) return;

      conversationId.current = response.conversation_id;
      setMessages((prev) => [
        ...prev,
        {
          id: response.message.id,
          role: response.message.role,
          content: response.message.content,
          createdAt: response.message.created_at,
          sources: response.sources,
        },
      ]);
    } catch (e) {
      if (version !== requestVersion.current) return;
      if (e instanceof Error && e.name === 'AbortError') return;
      const msg = e instanceof Error ? e.message : 'Something went wrong.';
      setError(msg);
    } finally {
      if (version === requestVersion.current) {
        activeRequest.current = null;
        setIsLoading(false);
        inFlight.current = false;
      }
    }
  }, []);

  const reset = useCallback(() => {
    requestVersion.current += 1;
    activeRequest.current?.abort();
    activeRequest.current = null;
    conversationId.current = null;
    inFlight.current = false;
    setMessages([welcomeMessage()]);
    setError(null);
    setIsLoading(false);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { messages, isLoading, error, send, reset, clearError };
}
