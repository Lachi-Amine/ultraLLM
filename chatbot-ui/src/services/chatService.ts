import { API_BASE_URL, API_TIMEOUT_MS } from '@/constants/config';
import type { ChatApiResponse } from '@/types/chat';

export class ChatApiError extends Error {
  constructor(
    message: string,
    public readonly status = 0,
  ) {
    super(message);
    this.name = 'ChatApiError';
  }
}

function isChatResponse(value: unknown): value is ChatApiResponse {
  if (!value || typeof value !== 'object') return false;
  const response = value as Partial<ChatApiResponse>;
  return (
    typeof response.conversation_id === 'string' &&
    !!response.message &&
    typeof response.message.id === 'string' &&
    typeof response.message.content === 'string' &&
    Array.isArray(response.sources) &&
    Array.isArray(response.warnings)
  );
}

export async function sendMessage(
  message: string,
  conversationId: string | null,
  callerSignal?: AbortSignal,
): Promise<ChatApiResponse> {
  const trimmed = message.trim();
  if (!trimmed) throw new ChatApiError('Message cannot be empty.');

  const controller = new AbortController();
  const cancelFromCaller = () => controller.abort();
  callerSignal?.addEventListener('abort', cancelFromCaller, { once: true });
  const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

  try {
    const response = await fetch(`${API_BASE_URL}/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: trimmed,
        conversation_id: conversationId,
      }),
      signal: controller.signal,
    });

    const body: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const detail =
        body && typeof body === 'object' && 'detail' in body
          ? String((body as { detail: unknown }).detail)
          : `Request failed with status ${response.status}.`;
      throw new ChatApiError(detail, response.status);
    }
    if (!isChatResponse(body)) {
      throw new ChatApiError('The backend returned an invalid response.');
    }
    return body;
  } catch (error) {
    if (error instanceof ChatApiError) throw error;
    if (error instanceof Error && error.name === 'AbortError') {
      if (callerSignal?.aborted) throw error;
      throw new ChatApiError('The request timed out.');
    }
    throw new ChatApiError(
      `Cannot reach the chatbot backend at ${API_BASE_URL}. Start the backend and check EXPO_PUBLIC_API_URL.`,
    );
  } finally {
    clearTimeout(timeout);
    callerSignal?.removeEventListener('abort', cancelFromCaller);
  }
}

export const chatEndpoint = `${API_BASE_URL}/v1/chat`;
