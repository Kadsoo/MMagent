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
            "messages": [self._serialize_message(message) for message in messages],
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
            if response.is_error:
                raise RuntimeError(
                    f"Provider error {response.status_code}: {response.text}"
                )
            data = response.json()
            return data["choices"][0]["message"]["content"]

    @staticmethod
    def _serialize_message(message: AgentMessage) -> dict[str, str]:
        # Many OpenAI-compatible providers accept the standard chat roles but
        # reject raw tool-role messages unless they follow official function
        # calling with tool_call_id. MMagent uses a custom JSON tool protocol,
        # so we fold tool observations back into the conversation as user-visible
        # context for the next reasoning turn.
        if message.role == "tool":
            tool_name = message.name or "tool"
            return {
                "role": "user",
                "content": f"Tool result from {tool_name}:\n{message.content}",
            }
        return {"role": message.role, "content": message.content}
