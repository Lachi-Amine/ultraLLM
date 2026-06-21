# Chatbot UI

Expo and React Native client for the local ultraLLM backend.

## Setup

Start the backend from the repository root first:

```bash
cd backend
uv sync --dev
uv run uvicorn app.main:app --reload
```

Then start the client:

```bash
cd chatbot-ui
cp .env.example .env
npm install
npm run web
```

The default API URL is `http://127.0.0.1:8000`.

When testing from a physical phone, set `EXPO_PUBLIC_API_URL` to the computer's
LAN address because the phone's `127.0.0.1` points to the phone itself.

## Features

- Real `/v1/chat` backend requests
- In-memory conversation continuity through `conversation_id`
- Request timeout and cancellation
- Reset-safe chat state
- Source-engine labels on assistant messages
- Enter to send and Shift+Enter for a new line on web
- Light and dark themes
- Web, iOS, and Android support through Expo

## Keyboard controls

- `Enter`: send the current message
- `Shift+Enter`: insert a new line

## Checks

```bash
npm test
npm run typecheck
npx expo-doctor
```
