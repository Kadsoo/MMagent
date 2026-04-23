from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from app.schemas.protocol import AgentMessage
from app.schemas.tool import ToolSpec


class BaseLLMAdapter(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: Sequence[AgentMessage],
        tools: Sequence[ToolSpec],
    ) -> str:
        """Return one JSON string following the MMagent protocol."""

