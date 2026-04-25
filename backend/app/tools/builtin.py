from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import Settings
from app.services.docs_service import DocsService
from app.services.time_service import TimeService
from app.services.todo_service import TodoService
from app.services.todo_store import TodoStore
from app.services.web_search_service import WebSearchService
from app.services.weather_service import WeatherService
from app.tools.context import ToolContext
from app.tools.registry import ToolRegistry
from app.utils.safe_eval import safe_calculate


class WeatherArgs(BaseModel):
    city: str = Field(description="City name, for example Nanjing or Beijing")


class TimeArgs(BaseModel):
    city: str | None = Field(default=None, description="City name")
    timezone: str | None = Field(default=None, description="IANA timezone")


class CalculatorArgs(BaseModel):
    expression: str = Field(description="Arithmetic expression with +, -, *, /, and ()")


class SearchDocsArgs(BaseModel):
    query: str = Field(description="Keyword query for local knowledge documents")


class WebSearchArgs(BaseModel):
    query: str = Field(description="Search query for internet lookup")
    max_results: int = Field(default=5, ge=1, le=8, description="Maximum related results")


class TodoAddArgs(BaseModel):
    item: str = Field(min_length=1, description="Todo item text")


class TodoListArgs(BaseModel):
    pass


class TodoDeleteArgs(BaseModel):
    index: int = Field(ge=1, description="1-based todo index in the current user's todo list")


class EmptyArgs(BaseModel):
    pass


def create_default_registry(
    todo_store: TodoStore,
    data_dir: Path,
    settings: Settings | None = None,
    todo_service: TodoService | None = None,
    weather_service: WeatherService | None = None,
    docs_service: DocsService | None = None,
    web_search_service: WebSearchService | None = None,
    time_service: TimeService | None = None,
) -> ToolRegistry:
    registry = ToolRegistry()

    resolved_weather_service = weather_service or _create_weather_service(settings)
    resolved_docs_service = docs_service or DocsService(data_dir=data_dir)
    resolved_web_search_service = web_search_service or WebSearchService()
    resolved_time_service = time_service or TimeService()
    resolved_todo_service = todo_service or TodoService(fallback_store=todo_store)

    registry.register(
        name="get_weather",
        description="Fetch real current weather for a city through Open-Meteo.",
        args_model=WeatherArgs,
        handler=lambda args: resolved_weather_service.get_weather(args.city),
    )
    registry.register(
        name="get_time",
        description="Return current local time for a city or IANA timezone using zoneinfo.",
        args_model=TimeArgs,
        handler=lambda args: resolved_time_service.get_time(args.city, args.timezone),
    )
    registry.register(
        name="calculator",
        description="Safely evaluate simple arithmetic expressions.",
        args_model=CalculatorArgs,
        handler=calculator,
    )
    registry.register(
        name="search_docs",
        description="Search real local project knowledge documents by keyword.",
        args_model=SearchDocsArgs,
        handler=lambda args: resolved_docs_service.search(args.query),
    )
    registry.register(
        name="web_search",
        description="Search the internet for topic summaries and related links.",
        args_model=WebSearchArgs,
        handler=lambda args: resolved_web_search_service.search(args.query, args.max_results),
    )
    registry.register(
        name="todo_add",
        description="Add a todo item for the current user. Uses MySQL when configured.",
        args_model=TodoAddArgs,
        handler=lambda args, context: resolved_todo_service.add(
            _require_context(context).user_id,
            args.item,
        ),
    )
    registry.register(
        name="todo_list",
        description="List todo items for the current user. Uses MySQL when configured.",
        args_model=TodoListArgs,
        handler=lambda args, context: resolved_todo_service.list(
            _require_context(context).user_id
        ),
    )
    registry.register(
        name="todo_delete",
        description="Delete a todo item from the current user's list by 1-based index.",
        args_model=TodoDeleteArgs,
        handler=lambda args, context: resolved_todo_service.delete(
            _require_context(context).user_id,
            args.index,
        ),
    )
    registry.register(
        name="get_system_status",
        description="Return runtime status and registered capability count.",
        args_model=EmptyArgs,
        handler=lambda args: get_system_status(registry),
    )
    return registry


def calculator(args: CalculatorArgs) -> dict[str, Any]:
    value = safe_calculate(args.expression)
    return {"expression": args.expression, "value": value, "source": "safe-ast"}


def get_system_status(registry: ToolRegistry) -> dict[str, Any]:
    return {
        "status": "ok",
        "registered_tools": len(registry.list_tools()),
        "llm_mode": "mock-or-configured",
        "runtime": "FastAPI AgentRuntime",
    }


def _create_weather_service(settings: Settings | None) -> WeatherService:
    if not settings:
        return WeatherService()
    return WeatherService(
        provider=settings.weather_provider,
        forecast_base_url=settings.weather_api_base_url,
        geocoding_base_url=settings.weather_geocoding_base_url,
        language=settings.weather_language,
        api_key=settings.weather_api_key,
    )


def _require_context(context: ToolContext | None) -> ToolContext:
    if not context:
        raise RuntimeError("Tool context is required for this operation.")
    return context
