# ultraLLM

ultraLLM is a local AI assistant created and developed by the APMA Team. It
combines a FastAPI backend, three domain-focused knowledge engines, optional
local language-model fallback, and an Expo/React Native chat client.

## Features

- APMA-branded ultraLLM identity
- Mathematics retrieval and symbolic calculation with SymPy
- Scientific and empirical knowledge retrieval
- Social and interpretive knowledge retrieval
- Optional local language-model fallback for general questions
- Conversation continuity through an in-memory conversation ID
- Web, iOS, and Android client support
- Enter to send and Shift+Enter for a new line on web
- Light and dark themes

## Architecture

```text
chatbot-ui (Expo / React Native)
        |
        | POST /v1/chat
        v
backend (FastAPI)
        |
        +-- Green engine: mathematics and symbolic calculations
        +-- Yellow engine: science and empirical knowledge
        +-- Red engine: social and interpretive knowledge
        +-- Local model fallback: general questions
```

Conversation data is stored in memory and resets when the backend restarts.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Ollama, if local model fallback is enabled

## Run locally

### 1. Start the backend

```bash
cd backend
uv sync --dev
uv run uvicorn app.main:app --reload
```

The API starts at [http://127.0.0.1:8000](http://127.0.0.1:8000).

To use a local fallback model, start Ollama, install a model, and provide its
name when starting the backend:

```bash
ollama serve
ollama pull <model-name>
OLLAMA_MODEL=<model-name> uv run uvicorn app.main:app --reload
```

To run only the deterministic knowledge engines:

```bash
OLLAMA_ENABLED=false uv run uvicorn app.main:app --reload
```

### 2. Start the web client

Open another terminal:

```bash
cd chatbot-ui
cp .env.example .env
npm install
npm run web
```

Open [http://localhost:8081](http://localhost:8081).

For a physical phone, replace `127.0.0.1` in `.env` with the computer's LAN IP,
then run `npm start` and open the project with Expo Go.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Backend and engine status |
| `POST` | `/v1/chat` | Send a chat message |
| `GET` | `/docs` | Interactive API documentation |

Example:

```bash
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"solve x^2 = 4"}'
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OLLAMA_ENABLED` | `true` | Enables local model fallback |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server URL |
| `OLLAMA_MODEL` | Backend default | Local model name |
| `OLLAMA_KEEP_ALIVE` | `2m` | Model keep-alive duration |
| `EXPO_PUBLIC_API_URL` | `http://127.0.0.1:8000` | Client API URL |

## Validation

Backend:

```bash
cd backend
uv run pytest
uv run ruff check app tests
```

Frontend:

```bash
cd chatbot-ui
npm test
npm run typecheck
npx expo-doctor
```

## Development scope

This repository is currently configured for local development. Authentication,
rate limiting, persistent conversation storage, and production deployment
configuration are not included.
