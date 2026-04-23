from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.memory import SessionStore
from app.agent.runtime import AgentRuntime
from app.api.routes import router
from app.core.config import DATA_DIR, get_settings
from app.core.logging import configure_logging
from app.llm.factory import create_llm_adapter
from app.services.todo_store import TodoStore
from app.tools.builtin import create_default_registry


settings = get_settings()
configure_logging(settings.app_env)

todo_store = TodoStore(DATA_DIR / "todos.json")
tool_registry = create_default_registry(todo_store=todo_store, data_dir=DATA_DIR)
llm_adapter = create_llm_adapter(settings)
session_store = SessionStore()
agent_runtime = AgentRuntime(
    llm=llm_adapter,
    registry=tool_registry,
    sessions=session_store,
    max_steps=settings.max_agent_steps,
)

app = FastAPI(
    title="MMagent API",
    description="A JSON Tool Calling multimodal-ready Agent runtime demo.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.settings = settings
app.state.registry = tool_registry
app.state.runtime = agent_runtime
app.state.todo_store = todo_store

app.include_router(router, prefix="/api")

