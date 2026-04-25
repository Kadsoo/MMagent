from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.conversation import ConversationRun
from app.schemas.protocol import AgentMessage, TraceStep


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    user_id: str = Field(min_length=2, max_length=64)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    user_id: str
    final_answer: str
    trace: list[TraceStep]
    messages: list[AgentMessage]
    runs: list[ConversationRun] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    service: str
