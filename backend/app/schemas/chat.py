from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.protocol import AgentMessage, TraceStep


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    final_answer: str
    trace: list[TraceStep]
    messages: list[AgentMessage]


class HealthResponse(BaseModel):
    status: str
    service: str

