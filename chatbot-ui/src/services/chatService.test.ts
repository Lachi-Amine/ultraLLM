import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('@/constants/config', () => ({
  API_BASE_URL: 'http://127.0.0.1:8000',
  API_TIMEOUT_MS: 20_000,
}));

import { ChatApiError, sendMessage } from './chatService';


afterEach(() => {
  vi.unstubAllGlobals();
});

describe('sendMessage', () => {
  it('posts the message and conversation id to the backend', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          conversation_id: 'conversation-1',
          message: {
            id: 'message-1',
            role: 'assistant',
            content: 'Velocity is directional speed.',
            created_at: '2026-06-21T00:00:00Z',
          },
          sources: [],
          warnings: [],
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    );
    vi.stubGlobal('fetch', fetchMock);

    const response = await sendMessage('What is velocity?', 'conversation-1');

    expect(response.message.content).toContain('Velocity');
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/v1/chat'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          message: 'What is velocity?',
          conversation_id: 'conversation-1',
        }),
      }),
    );
  });

  it('rejects invalid response bodies', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ reply: 'old contract' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    await expect(sendMessage('hello', null)).rejects.toThrow(
      'The backend returned an invalid response.',
    );
  });

  it('surfaces backend validation errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: 'Message is invalid.' }), {
          status: 422,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    await expect(sendMessage('hello', null)).rejects.toEqual(
      new ChatApiError('Message is invalid.', 422),
    );
  });
});
