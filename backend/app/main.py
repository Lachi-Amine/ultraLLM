from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    GREEN_DATA_PATH,
    OLLAMA_BASE_URL,
    OLLAMA_ENABLED,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_MODEL,
    RED_DATA_PATH,
    YELLOW_DATA_PATH,
)
from .engines import GreenEngine, RedEngine, YellowEngine
from .schemas import ChatRequest, ChatResponse, HealthResponse
from .services.orchestrator import ChatOrchestrator
from .services.ollama import OllamaClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.orchestrator = ChatOrchestrator(
        green=GreenEngine(GREEN_DATA_PATH),
        yellow=YellowEngine(YELLOW_DATA_PATH),
        red=RedEngine(RED_DATA_PATH),
        llm=OllamaClient(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            enabled=OLLAMA_ENABLED,
            keep_alive=OLLAMA_KEEP_ALIVE,
        ),
    )
    yield


app = FastAPI(title="ultraLLM Dev Chatbot", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:19006",
        "http://127.0.0.1:19006",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ultraLLM development backend"}


@app.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    orchestrator: ChatOrchestrator = request.app.state.orchestrator
    return HealthResponse(status="ok", engines=orchestrator.engine_counts)


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    orchestrator: ChatOrchestrator = request.app.state.orchestrator
    return await orchestrator.chat(payload.message, payload.conversation_id)
