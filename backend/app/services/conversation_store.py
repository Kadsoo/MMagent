from __future__ import annotations

import json
import logging
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator
from urllib.parse import quote_plus

import pymysql
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.agent.memory import ConversationMemory
from app.core.config import Settings
from app.db.models import Base, ConversationMessageModel, ConversationModel, ConversationRunModel
from app.schemas.conversation import ConversationDetail, ConversationRun, ConversationSummary
from app.schemas.protocol import AgentMessage, TraceStep


logger = logging.getLogger(__name__)


class MySQLConversationStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._ensure_database()
        self.engine = create_engine(
            self._database_url(),
            pool_pre_ping=True,
            pool_recycle=3600,
            future=True,
        )
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)
        Base.metadata.create_all(self.engine)

    def load_memory(self, user_id: str, session_id: str) -> ConversationMemory | None:
        detail = self.get_conversation_detail(user_id=user_id, session_id=session_id)
        if not detail:
            return None
        trace_history = [step for run in detail.runs for step in run.trace]
        return ConversationMemory(
            session_id=detail.session_id,
            user_id=detail.user_id,
            title=detail.title,
            messages=detail.messages,
            trace_history=trace_history,
            runs=detail.runs,
        )

    def save_conversation(
        self,
        memory: ConversationMemory,
        user_input: str,
        final_answer: str,
        trace: list[TraceStep],
    ) -> None:
        with self._session_scope() as db:
            conversation = self._get_or_create_conversation(
                db=db,
                user_id=memory.user_id,
                session_id=memory.session_id,
            )
            conversation.title = memory.title or self._derive_title(memory.messages)
            conversation.last_message_preview = (final_answer or user_input)[:255]
            conversation.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            conversation.messages = [
                ConversationMessageModel(
                    position=index,
                    role=message.role,
                    name=message.name,
                    content=message.content,
                )
                for index, message in enumerate(memory.messages)
            ]
            conversation.runs.append(
                ConversationRunModel(
                    user_input=user_input,
                    final_answer=final_answer,
                    trace_json=json.dumps(
                        [step.model_dump() for step in trace],
                        ensure_ascii=False,
                    ),
                )
            )
            db.add(conversation)

    def list_conversations(self, user_id: str) -> list[ConversationSummary]:
        with self._session_scope() as db:
            rows = db.scalars(
                select(ConversationModel)
                .where(ConversationModel.user_id == user_id)
                .order_by(ConversationModel.updated_at.desc(), ConversationModel.id.desc())
            ).all()
            return [self._to_summary(row) for row in rows]

    def get_conversation_detail(
        self,
        user_id: str,
        session_id: str,
    ) -> ConversationDetail | None:
        with self._session_scope() as db:
            row = db.scalar(
                select(ConversationModel)
                .where(
                    ConversationModel.user_id == user_id,
                    ConversationModel.session_id == session_id,
                )
                .options(
                    selectinload(ConversationModel.messages),
                    selectinload(ConversationModel.runs),
                )
            )
            if not row:
                return None
            return self._to_detail(row)

    def rename_conversation(
        self,
        user_id: str,
        session_id: str,
        title: str,
    ) -> ConversationDetail | None:
        with self._session_scope() as db:
            row = db.scalar(
                select(ConversationModel)
                .where(
                    ConversationModel.user_id == user_id,
                    ConversationModel.session_id == session_id,
                )
                .options(
                    selectinload(ConversationModel.messages),
                    selectinload(ConversationModel.runs),
                )
            )
            if not row:
                return None
            row.title = title[:80]
            row.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.flush()
            return self._to_detail(row)

    def _get_or_create_conversation(
        self,
        db: Session,
        user_id: str,
        session_id: str,
    ) -> ConversationModel:
        row = db.scalar(
            select(ConversationModel).where(
                ConversationModel.user_id == user_id,
                ConversationModel.session_id == session_id,
            )
        )
        if row:
            return row
        row = ConversationModel(
            user_id=user_id,
            session_id=session_id,
            title="New Conversation",
        )
        db.add(row)
        db.flush()
        return row

    def _to_summary(self, row: ConversationModel) -> ConversationSummary:
        return ConversationSummary(
            session_id=row.session_id,
            user_id=row.user_id,
            title=row.title,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_message_preview=row.last_message_preview,
        )

    def _to_detail(self, row: ConversationModel) -> ConversationDetail:
        messages = [
            AgentMessage(role=message.role, content=message.content, name=message.name)
            for message in sorted(row.messages, key=lambda item: item.position)
        ]
        runs = [
            ConversationRun(
                id=run.id,
                user_input=run.user_input,
                final_answer=run.final_answer,
                trace=[
                    TraceStep.model_validate(step)
                    for step in json.loads(run.trace_json)
                ],
                created_at=run.created_at,
            )
            for run in sorted(row.runs, key=lambda item: item.created_at)
        ]
        return ConversationDetail(
            session_id=row.session_id,
            user_id=row.user_id,
            title=row.title,
            created_at=row.created_at,
            updated_at=row.updated_at,
            last_message_preview=row.last_message_preview,
            messages=messages,
            runs=runs,
        )

    def _ensure_database(self) -> None:
        database_name = self.settings.mysql_database
        if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
            raise ValueError("MYSQL_DATABASE may only contain letters, numbers, and underscores.")
        connection = pymysql.connect(
            host=self.settings.mysql_host,
            port=self.settings.mysql_port,
            user=self.settings.mysql_user,
            password=self.settings.mysql_password,
            charset=self.settings.mysql_charset,
            autocommit=True,
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
        finally:
            connection.close()

    def _database_url(self) -> str:
        return (
            f"mysql+pymysql://{quote_plus(self.settings.mysql_user)}:{quote_plus(self.settings.mysql_password)}"
            f"@{self.settings.mysql_host}:{self.settings.mysql_port}/{self.settings.mysql_database}"
            f"?charset={self.settings.mysql_charset}"
        )

    @contextmanager
    def _session_scope(self) -> Iterator[Session]:
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

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


def create_conversation_store(settings: Settings) -> MySQLConversationStore | None:
    try:
        store = MySQLConversationStore(settings)
        logger.info(
            "MySQL conversation store enabled for %s:%s/%s",
            settings.mysql_host,
            settings.mysql_port,
            settings.mysql_database,
        )
        return store
    except Exception as exc:  # pragma: no cover
        logger.warning(
            "MySQL conversation store unavailable, falling back to in-memory sessions: %s",
            exc,
        )
        return None
