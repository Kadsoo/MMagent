from __future__ import annotations

from app.core.config import Settings
from app.llm.base import BaseLLMAdapter
from app.llm.mock import MockLLMAdapter
from app.llm.openai_compatible import OpenAICompatibleAdapter


def create_llm_adapter(settings: Settings) -> BaseLLMAdapter:
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAICompatibleAdapter(
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    return MockLLMAdapter()

