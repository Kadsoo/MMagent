from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.memory import SessionStore
from app.agent.runtime import AgentRuntime
from app.api.routes import router
from app.core.config import DATA_DIR, get_settings
from app.core.logging import configure_logging
from app.llm.factory import create_llm_adapter
from app.services.conversation_store import create_conversation_store
from app.services.docs_service import DocsService
from app.services.time_service import TimeService
from app.services.todo_service import TodoService
from app.services.todo_store import TodoStore
from app.services.web_search_service import WebSearchService
from app.services.weather_service import WeatherService
from app.tools.builtin import create_default_registry


settings = get_settings()
configure_logging(settings.app_env)

todo_store = TodoStore(DATA_DIR / "todos.json")
llm_adapter = create_llm_adapter(settings)
conversation_store = create_conversation_store(settings)
todo_service = TodoService(
    fallback_store=todo_store,
    session_factory=getattr(conversation_store, "SessionLocal", None),
)
weather_service = WeatherService(
    provider=settings.weather_provider,
    forecast_base_url=settings.weather_api_base_url,
    geocoding_base_url=settings.weather_geocoding_base_url,
    language=settings.weather_language,
    api_key=settings.weather_api_key,
)
tool_registry = create_default_registry(
    todo_store=todo_store,
    data_dir=DATA_DIR,
    settings=settings,
    todo_service=todo_service,
    weather_service=weather_service,
    docs_service=DocsService(DATA_DIR),
    web_search_service=WebSearchService(settings.web_search_base_url),
    time_service=TimeService(),
)
session_store = SessionStore(conversation_store=conversation_store)
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
app.state.todo_service = todo_service
app.state.sessions = session_store
app.state.conversation_store = conversation_store

app.include_router(router, prefix="/api")
