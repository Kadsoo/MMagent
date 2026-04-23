from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any


class TodoStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]\n", encoding="utf-8")

    def list_items(self) -> list[str]:
        with self._lock:
            return list(self._read())

    def count(self) -> int:
        return len(self.list_items())

    def add_item(self, item: str) -> dict[str, Any]:
        clean_item = item.strip()
        if not clean_item:
            raise ValueError("Todo item cannot be empty.")
        with self._lock:
            items = self._read()
            items.append(clean_item)
            self._write(items)
            return {"item": clean_item, "index": len(items), "count": len(items)}

    def delete_item(self, index: int) -> dict[str, Any]:
        with self._lock:
            items = self._read()
            if index < 1 or index > len(items):
                raise ValueError(f"Todo index out of range: {index}")
            deleted = items.pop(index - 1)
            self._write(items)
            return {
                "deleted_item": deleted,
                "deleted_index": index,
                "items": items,
                "count": len(items),
            }

    def _read(self) -> list[str]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Todo store is corrupted.") from exc
        if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
            raise ValueError("Todo store must be a JSON array of strings.")
        return data

    def _write(self, items: list[str]) -> None:
        tmp_path = self.path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)

