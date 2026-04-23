from __future__ import annotations

from collections.abc import Sequence

import httpx

from app.llm.base import BaseLLMAdapter
from app.schemas.protocol import AgentMessage
from app.schemas.tool import ToolSpec


class OpenAICompatibleAdapter(BaseLLMAdapter):
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        messages: Sequence[AgentMessage],
        tools: Sequence[ToolSpec],
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": message.role, "content": message.content}
                if message.role != "tool"
                else {
                    "role": "tool",
                    "name": message.name or "tool",
                    "content": message.content,
                }
                for message in messages
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

