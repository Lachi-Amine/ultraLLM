from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


EngineName = Literal["green", "yellow", "red", "system"]
EvidenceStatus = Literal["success", "fallback", "failed"]


class Query(BaseModel):
    text: str
    tokens: list[str] = Field(default_factory=list)
    intent: str = "general"
    domain: str = "unknown"


class EvidenceRecord(BaseModel):
    engine_type: EngineName
    status: EvidenceStatus
    output: str
    top_passages: list[str] = Field(default_factory=list)
    trace: list[str] = Field(default_factory=list)
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    domain: str = "unknown"
    intent: str = "general"
    source: str = "unknown"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4_000)
    conversation_id: UUID | None = None


class ChatMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SourceRecord(BaseModel):
    engine: EngineName
    domain: str
    intent: str
    score: float
    content: str
    source: str


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: ChatMessage
    sources: list[SourceRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    engines: dict[str, int]
