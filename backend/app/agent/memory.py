from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.schemas.protocol import AgentMessage, TraceStep


@dataclass
class ConversationMemory:
    session_id: str
    messages: list[AgentMessage] = field(default_factory=list)
    trace_history: list[TraceStep] = field(default_factory=list)

    def add_message(self, role: str, content: str, name: str | None = None) -> None:
        self.messages.append(AgentMessage(role=role, content=content, name=name))

    def extend_trace(self, steps: list[TraceStep]) -> None:
        self.trace_history.extend(steps)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, ConversationMemory] = {}

    def get_or_create(self, session_id: str | None = None) -> ConversationMemory:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]

        new_session_id = session_id or str(uuid4())
        memory = ConversationMemory(session_id=new_session_id)
        self._sessions[new_session_id] = memory
        return memory

