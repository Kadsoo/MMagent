from __future__ import annotations

from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.services.todo_store import TodoStore
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


class TodoAddArgs(BaseModel):
    item: str = Field(min_length=1, description="Todo item text")


class TodoListArgs(BaseModel):
    pass


class TodoDeleteArgs(BaseModel):
    index: int = Field(ge=1, description="1-based todo index")


class EmptyArgs(BaseModel):
    pass


class MapLookupArgs(BaseModel):
    location: str = Field(description="Game location, e.g. forest, castle, village")


def create_default_registry(todo_store: TodoStore, data_dir: Path) -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(
        name="get_weather",
        description="Return mock weather for a city.",
        args_model=WeatherArgs,
        handler=get_weather,
    )
    registry.register(
        name="get_time",
        description="Return current local time for a city or IANA timezone.",
        args_model=TimeArgs,
        handler=get_time,
    )
    registry.register(
        name="calculator",
        description="Safely evaluate simple arithmetic expressions.",
        args_model=CalculatorArgs,
        handler=calculator,
    )
    registry.register(
        name="search_docs",
        description="Search local project knowledge documents by keyword.",
        args_model=SearchDocsArgs,
        handler=lambda args: search_docs(args, data_dir),
    )
    registry.register(
        name="todo_add",
        description="Add a todo item to the local todo store.",
        args_model=TodoAddArgs,
        handler=lambda args: todo_store.add_item(args.item),
    )
    registry.register(
        name="todo_list",
        description="List all todo items.",
        args_model=TodoListArgs,
        handler=lambda args: {"items": todo_store.list_items(), "count": todo_store.count()},
    )
    registry.register(
        name="todo_delete",
        description="Delete a todo item by 1-based index.",
        args_model=TodoDeleteArgs,
        handler=lambda args: todo_store.delete_item(args.index),
    )
    registry.register(
        name="get_system_status",
        description="Return runtime status and registered capability count.",
        args_model=EmptyArgs,
        handler=lambda args: get_system_status(registry),
    )
    registry.register(
        name="map_lookup",
        description="Demo game-AI extension point for querying map observations.",
        args_model=MapLookupArgs,
        handler=map_lookup,
    )
    return registry


def get_weather(args: WeatherArgs) -> dict[str, Any]:
    weather_data = {
        "nanjing": {"temperature": "26C", "condition": "Sunny", "humidity": "48%"},
        "beijing": {"temperature": "22C", "condition": "Cloudy", "humidity": "35%"},
        "shanghai": {"temperature": "24C", "condition": "Light rain", "humidity": "71%"},
        "shenzhen": {"temperature": "29C", "condition": "Humid", "humidity": "76%"},
        "hangzhou": {"temperature": "25C", "condition": "Partly cloudy", "humidity": "63%"},
        "tokyo": {"temperature": "20C", "condition": "Clear", "humidity": "52%"},
        "new york": {"temperature": "18C", "condition": "Windy", "humidity": "44%"},
    }
    city_key = args.city.strip().lower()
    payload = weather_data.get(
        city_key,
        {"temperature": "23C", "condition": "Unknown mock weather", "humidity": "50%"},
    )
    return {"city": args.city, **payload, "source": "mock"}


def get_time(args: TimeArgs) -> dict[str, str]:
    city_to_timezone = {
        "nanjing": "Asia/Shanghai",
        "beijing": "Asia/Shanghai",
        "shanghai": "Asia/Shanghai",
        "shenzhen": "Asia/Shanghai",
        "hangzhou": "Asia/Shanghai",
        "tokyo": "Asia/Tokyo",
        "new york": "America/New_York",
        "london": "Europe/London",
    }
    target = args.timezone or city_to_timezone.get((args.city or "").lower(), "UTC")
    target, zone = _resolve_timezone(target)
    now = datetime.now(zone)
    return {
        "city_or_timezone": args.city or target,
        "timezone": target,
        "local_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "iso": now.isoformat(),
    }


def calculator(args: CalculatorArgs) -> dict[str, Any]:
    value = safe_calculate(args.expression)
    return {"expression": args.expression, "value": value}


def search_docs(args: SearchDocsArgs, data_dir: Path) -> dict[str, Any]:
    query = args.query.strip().lower()
    files = list(data_dir.glob("*.md")) + list(data_dir.glob("*.txt"))
    matches: list[dict[str, Any]] = []
    query_terms = [term for term in query.split() if len(term) > 1]

    for path in files:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        score = sum(lowered.count(term) for term in query_terms)
        if not score and query in lowered:
            score = 1
        if score:
            snippet = _make_snippet(text, query_terms)
            matches.append({"file": path.name, "score": score, "snippet": snippet})

    matches.sort(key=lambda item: item["score"], reverse=True)
    if matches:
        summary = matches[0]["snippet"]
    else:
        summary = "No exact keyword match. Try queries like runtime, tool calling, registry, or game agent."

    return {"query": args.query, "summary": summary, "matches": matches[:5]}


def get_system_status(registry: ToolRegistry) -> dict[str, Any]:
    return {
        "status": "ok",
        "registered_tools": len(registry.list_tools()),
        "llm_mode": "mock-or-configured",
        "runtime": "FastAPI AgentRuntime",
    }


def map_lookup(args: MapLookupArgs) -> dict[str, Any]:
    maps = {
        "forest": {
            "summary": "two enemies near the north path and one health potion",
            "enemies": [{"type": "slime", "x": 4, "y": 8}, {"type": "archer", "x": 7, "y": 9}],
            "items": [{"name": "health_potion", "x": 2, "y": 3}],
        },
        "castle": {
            "summary": "a locked gate, one elite guard, and a treasure chest",
            "enemies": [{"type": "guard", "x": 5, "y": 2}],
            "items": [{"name": "silver_key", "x": 1, "y": 6}],
        },
        "village": {
            "summary": "no enemies, one merchant, and a quest board",
            "enemies": [],
            "items": [{"name": "quest_board", "x": 3, "y": 1}],
        },
        "森林": {
            "summary": "two enemies near the north path and one health potion",
            "enemies": [{"type": "slime", "x": 4, "y": 8}, {"type": "archer", "x": 7, "y": 9}],
            "items": [{"name": "health_potion", "x": 2, "y": 3}],
        },
        "城堡": {
            "summary": "a locked gate, one elite guard, and a treasure chest",
            "enemies": [{"type": "guard", "x": 5, "y": 2}],
            "items": [{"name": "silver_key", "x": 1, "y": 6}],
        },
    }
    location = args.location.strip().lower()
    info = maps.get(location, maps["forest"])
    return {"location": args.location, **info}


def _make_snippet(text: str, terms: list[str]) -> str:
    lowered = text.lower()
    index = 0
    for term in terms:
        index = lowered.find(term)
        if index >= 0:
            break
    start = max(index - 120, 0)
    end = min(index + 280, len(text))
    snippet = text[start:end].replace("\n", " ").strip()
    return " ".join(snippet.split())


def _resolve_timezone(target: str) -> tuple[str, tzinfo]:
    try:
        return target, ZoneInfo(target)
    except Exception:
        fixed_offsets = {
            "UTC": timezone.utc,
            "Asia/Shanghai": timezone(timedelta(hours=8), name="Asia/Shanghai"),
            "Asia/Tokyo": timezone(timedelta(hours=9), name="Asia/Tokyo"),
            "America/New_York": timezone(timedelta(hours=-4), name="America/New_York"),
            "Europe/London": timezone(timedelta(hours=1), name="Europe/London"),
        }
        if target in fixed_offsets:
            return target, fixed_offsets[target]
        return "UTC", timezone.utc
