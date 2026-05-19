import { useCallback, useRef, useState } from 'react';

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

  // Guard against double-send races (e.g. rapid taps).
  const inFlight = useRef(false);

  const send = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || inFlight.current) return;

    inFlight.current = true;
    setError(null);
    setIsLoading(true);

    const userMsg = makeMessage('user', trimmed);
    setMessages((prev) => [...prev, userMsg]);

    try {
      const reply = await sendMessage(trimmed);
      setMessages((prev) => [...prev, makeMessage('assistant', reply)]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Something went wrong.';
      setError(msg);
    } finally {
      setIsLoading(false);
      inFlight.current = false;
    }
  }, []);

  const reset = useCallback(() => {
    setMessages([welcomeMessage()]);
    setError(null);
    setIsLoading(false);
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { messages, isLoading, error, send, reset, clearError };
}
