from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolContext:
    user_id: str
    session_id: str
