from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from app.schemas.conversation import ConversationDetail, ConversationRun, ConversationSummary
from app.schemas.protocol import AgentMessage, TraceStep


@dataclass
class ConversationMemory:
    session_id: str
    user_id: str
    title: str | None = None
    messages: list[AgentMessage] = field(default_factory=list)
    trace_history: list[TraceStep] = field(default_factory=list)
    runs: list[ConversationRun] = field(default_factory=list)

    def add_message(self, role: str, content: str, name: str | None = None) -> None:
        self.messages.append(AgentMessage(role=role, content=content, name=name))

    def extend_trace(self, steps: list[TraceStep]) -> None:
        self.trace_history.extend(steps)


class SessionStore:
    def __init__(self, conversation_store: object | None = None) -> None:
        self._sessions: dict[str, ConversationMemory] = {}
        self._conversation_store = conversation_store

    def get_or_create(self, user_id: str, session_id: str | None = None) -> ConversationMemory:
        if session_id and session_id in self._sessions:
            memory = self._sessions[session_id]
            if memory.user_id == user_id:
                return memory

        if session_id and self._conversation_store:
            loaded = self._conversation_store.load_memory(
                user_id=user_id,
                session_id=session_id,
            )
            if loaded:
                self._sessions[loaded.session_id] = loaded
                return loaded

        new_session_id = session_id or str(uuid4())
        memory = ConversationMemory(session_id=new_session_id, user_id=user_id)
        self._sessions[new_session_id] = memory
        return memory

    def record_run(
        self,
        memory: ConversationMemory,
        user_input: str,
        final_answer: str,
        trace: list[TraceStep],
    ) -> None:
        memory.extend_trace(trace)
        memory.runs.append(
            ConversationRun(
                user_input=user_input,
                final_answer=final_answer,
                trace=trace,
                created_at=datetime.now(timezone.utc),
            )
        )
        if self._conversation_store:
            self._conversation_store.save_conversation(
                memory=memory,
                user_input=user_input,
                final_answer=final_answer,
                trace=trace,
            )

    def list_conversations(self, user_id: str) -> list[ConversationSummary]:
        if self._conversation_store:
            rows = self._conversation_store.list_conversations(user_id=user_id)
            if rows:
                return rows

        now = datetime.now(timezone.utc)
        return [
            ConversationSummary(
                session_id=memory.session_id,
                user_id=memory.user_id,
                title=self._derive_title(memory.messages),
                created_at=memory.runs[0].created_at if memory.runs else now,
                updated_at=memory.runs[-1].created_at if memory.runs else now,
                last_message_preview=memory.runs[-1].final_answer[:255] if memory.runs else None,
            )
            for memory in self._sessions.values()
            if memory.user_id == user_id
        ]

    def get_conversation_detail(
        self,
        user_id: str,
        session_id: str,
    ) -> ConversationDetail | None:
        if self._conversation_store:
            detail = self._conversation_store.get_conversation_detail(
                user_id=user_id,
                session_id=session_id,
            )
            if detail:
                return detail

        memory = self._sessions.get(session_id)
        if not memory or memory.user_id != user_id:
            return None

        now = datetime.now(timezone.utc)
        return ConversationDetail(
            session_id=memory.session_id,
            user_id=memory.user_id,
            title=memory.title or self._derive_title(memory.messages),
            created_at=memory.runs[0].created_at if memory.runs else now,
            updated_at=memory.runs[-1].created_at if memory.runs else now,
            last_message_preview=memory.runs[-1].final_answer[:255] if memory.runs else None,
            messages=memory.messages,
            runs=memory.runs,
        )

    def rename_conversation(
        self,
        user_id: str,
        session_id: str,
        title: str,
    ) -> ConversationDetail | None:
        clean_title = " ".join(title.split())
        if not clean_title:
            raise ValueError("Conversation title cannot be empty.")

        if self._conversation_store:
            detail = self._conversation_store.rename_conversation(
                user_id=user_id,
                session_id=session_id,
                title=clean_title,
            )
            if detail:
                loaded = self._conversation_store.load_memory(
                    user_id=user_id,
                    session_id=session_id,
                )
                if loaded:
                    self._sessions[loaded.session_id] = loaded
                return detail

        memory = self._sessions.get(session_id)
        if not memory or memory.user_id != user_id:
            return None
        memory.title = clean_title
        return self.get_conversation_detail(user_id=user_id, session_id=session_id)

    @staticmethod
    def _derive_title(messages: list[AgentMessage]) -> str:
        first_user_message = next(
            (message.content.strip() for message in messages if message.role == "user"),
            "New Conversation",
        )
        compact = " ".join(first_user_message.split())
        if len(compact) <= 48:
            return compact or "New Conversation"
        return f"{compact[:45]}..."
