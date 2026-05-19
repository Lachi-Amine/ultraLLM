import { API_BASE_URL, API_TIMEOUT_MS } from '@/constants/config';

const MOCK_REPLIES = [
  "Got it. Tell me more.",
  "Interesting — could you clarify what you mean?",
  "Here's what I'd suggest: start small and iterate.",
  "That's a great question. The short answer is: it depends.",
  "Sure — happy to help with that.",
];

function pickMockReply(input: string): string {
  const idx = Math.abs(hashString(input)) % MOCK_REPLIES.length;
  return MOCK_REPLIES[idx];
}

function hashString(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h << 5) - h + s.charCodeAt(i);
  return h | 0;
}

/**
 * Send a user message and resolve with the assistant's reply.
 *
 * Replace the mock block with a real HTTP call when the backend is ready:
 *
 *   const res = await fetch(`${API_BASE_URL}/chat`, {
 *     method: 'POST',
 *     headers: { 'Content-Type': 'application/json' },
 *     body: JSON.stringify({ message }),
 *     signal: AbortSignal.timeout(API_TIMEOUT_MS),
 *   });
 *   if (!res.ok) throw new Error(`Request failed: ${res.status}`);
 *   const data = (await res.json()) as { reply: string };
 *   return data.reply;
 */
export async function sendMessage(message: string): Promise<string> {
  // --- MOCK START (remove when wiring up the real API) ---
  await new Promise((resolve) => setTimeout(resolve, 700 + Math.random() * 600));
  if (!message.trim()) throw new Error('Empty message');
  return pickMockReply(message);
  // --- MOCK END ---
}

// Exported for convenience so the base URL is referenced and easy to find.
export const chatEndpoint = `${API_BASE_URL}/chat`;
