from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[3]
APP_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = APP_DIR / "data"


class Settings(BaseModel):
    app_env: str = Field(default="local")
    backend_cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    max_agent_steps: int = Field(default=6, ge=1, le=12)

    llm_provider: str = Field(default="mock")
    openai_base_url: str = Field(default="https://api.openai.com/v1")
    openai_api_key: str | None = None
    openai_model: str = Field(default="gpt-4o-mini")


def _split_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    return Settings(
        app_env=os.getenv("APP_ENV", "local"),
        backend_cors_origins=_split_csv(
            os.getenv("BACKEND_CORS_ORIGINS"), default_origins
        ),
        max_agent_steps=int(os.getenv("MAX_AGENT_STEPS", "6")),
        llm_provider=os.getenv("LLM_PROVIDER", "mock").lower(),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )

