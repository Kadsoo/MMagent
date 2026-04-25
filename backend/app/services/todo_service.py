from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import sessionmaker

from app.db.models import TodoModel
from app.services.todo_store import TodoStore


class TodoService:
    def __init__(
        self,
        fallback_store: TodoStore,
        session_factory: sessionmaker | None = None,
    ) -> None:
        self.fallback_store = fallback_store
        self.session_factory = session_factory

    def add(self, user_id: str, item: str) -> dict[str, Any]:
        clean_item = item.strip()
        if not clean_item:
            raise ValueError("Todo item cannot be empty.")

        if not self.session_factory:
            return {**self.fallback_store.add_item(clean_item), "source": "json-fallback"}

        with self.session_factory() as session:
            todo = TodoModel(user_id=user_id, content=clean_item, status="open")
            session.add(todo)
            session.commit()
            session.refresh(todo)
            return {
                "id": todo.id,
                "index": todo.id,
                "item": todo.content,
                "status": todo.status,
                "source": "mysql",
            }

    def list(self, user_id: str) -> dict[str, Any]:
        if not self.session_factory:
            items = self.fallback_store.list_items()
            return {
                "items": items,
                "count": len(items),
                "source": "json-fallback",
            }

        with self.session_factory() as session:
            rows = session.scalars(
                select(TodoModel)
                .where(TodoModel.user_id == user_id)
                .order_by(TodoModel.id.asc())
            ).all()
            items = [
                {
                    "id": row.id,
                    "item": row.content,
                    "status": row.status,
                    "created_at": row.created_at.isoformat()
                    if row.created_at
                    else None,
                }
                for row in rows
            ]
            return {
                "items": items,
                "count": len(items),
                "source": "mysql",
            }

    def delete(self, user_id: str, index: int) -> dict[str, Any]:
        if not self.session_factory:
            return {**self.fallback_store.delete_item(index), "source": "json-fallback"}

        with self.session_factory() as session:
            rows = session.scalars(
                select(TodoModel)
                .where(TodoModel.user_id == user_id)
                .order_by(TodoModel.id.asc())
            ).all()
            if index < 1 or index > len(rows):
                raise ValueError(f"Todo index out of range: {index}")
            target = rows[index - 1]
            deleted_payload = {
                "deleted_id": target.id,
                "deleted_index": index,
                "deleted_item": target.content,
            }
            session.execute(delete(TodoModel).where(TodoModel.id == target.id))
            session.commit()
            return {
                **deleted_payload,
                "count": len(rows) - 1,
                "source": "mysql",
            }

    def list_text_items(self, user_id: str | None = None) -> list[str]:
        if self.session_factory and user_id:
            result = self.list(user_id)
            return [item["item"] for item in result["items"]]
        return self.fallback_store.list_items()
