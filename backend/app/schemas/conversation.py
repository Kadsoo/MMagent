from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.protocol import AgentMessage, TraceStep


class ConversationRun(BaseModel):
    id: int | None = None
    user_input: str
    final_answer: str
    trace: list[TraceStep] = Field(default_factory=list)
    created_at: datetime


class ConversationSummary(BaseModel):
    session_id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    last_message_preview: str | None = None


class ConversationDetail(ConversationSummary):
    messages: list[AgentMessage] = Field(default_factory=list)
    runs: list[ConversationRun] = Field(default_factory=list)
