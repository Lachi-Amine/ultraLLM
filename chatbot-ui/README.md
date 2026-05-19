# Chatbot UI

A minimal mobile chatbot frontend built with **Expo + React Native + TypeScript**.
Single screen, no auth, no storage — wired to swap a mock service for a real
backend in one place.

## Setup

```bash
npm install
npx expo start
```

Then press `i` for iOS simulator, `a` for Android emulator, or scan the QR code
with the Expo Go app on your device. (For SDK 52, Expo Go is supported; you can
also build a dev client if you need native modules later.)

## Project structure

```
app/
  _layout.tsx          # Root Stack + SafeAreaProvider + StatusBar
  index.tsx            # Chat screen
src/
  components/
    MessageBubble.tsx  # Single message rendered as a bubble
    ChatInput.tsx      # Text input + Send button
    TypingIndicator.tsx# "Assistant is typing…"
  hooks/
    useChat.ts         # Chat state: messages, isLoading, error, send, reset
  services/
    chatService.ts     # sendMessage(message) — MOCK; swap for fetch()
  types/
    chat.ts            # Message and Role types
  constants/
    config.ts          # API_BASE_URL, colors (light + dark), welcome text
assets/                # icons / splash (placeholder README inside)
app.json               # Expo config — `extra.apiBaseUrl` lives here
```

## Replacing the mock with a real backend

1. Open [src/services/chatService.ts](src/services/chatService.ts).
2. Delete the block between `--- MOCK START ---` and `--- MOCK END ---`.
3. Uncomment / paste the `fetch` example shown in the JSDoc above the function:

   ```ts
   const res = await fetch(`${API_BASE_URL}/chat`, {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ message }),
     signal: AbortSignal.timeout(API_TIMEOUT_MS),
   });
   if (!res.ok) throw new Error(`Request failed: ${res.status}`);
   const data = (await res.json()) as { reply: string };
   return data.reply;
   ```

4. Set your backend URL in [app.json](app.json) under `expo.extra.apiBaseUrl`.
   It's read at runtime via `expo-constants` in
   [src/constants/config.ts](src/constants/config.ts), so changing it requires
   only an app reload — no rebuild.

## Features

- Single-screen scrollable chat using `FlatList`
- `user` and `assistant` message bubbles with distinct alignment + colors
- Bottom text input with a Send button (disabled when empty or loading)
- `ActivityIndicator` + "Assistant is typing…" while awaiting a reply
- Automatic scroll to the latest message
- `KeyboardAvoidingView` for iOS, `SafeAreaView` on top + bottom edges
- Pull-to-refresh resets the chat
- Tap-to-dismiss inline error banner if the API call fails
- Light and dark themes via `useColorScheme` — palette in `constants/config.ts`

## Notes

- React Native's `newArchEnabled: true` is on in `app.json`. Disable it in
  `app.json` if a native module you add later doesn't yet support the new
  architecture.
- The `@/` path alias maps to `src/` (see [tsconfig.json](tsconfig.json)).
