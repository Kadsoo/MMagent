from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.agent.runtime import AgentRuntime
from app.schemas.chat import ChatRequest, ChatResponse, HealthResponse
from app.schemas.tool import ToolSpec
from app.services.todo_store import TodoStore
from app.tools.registry import ToolRegistry


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="MMagent")


@router.get("/tools", response_model=list[ToolSpec])
async def list_tools(request: Request) -> list[ToolSpec]:
    registry: ToolRegistry = request.app.state.registry
    return registry.list_tools()


@router.get("/todos", response_model=list[str])
async def list_todos(request: Request) -> list[str]:
    todo_store: TodoStore = request.app.state.todo_store
    return todo_store.list_items()


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    runtime: AgentRuntime = request.app.state.runtime
    try:
        return await runtime.run(payload.message, session_id=payload.session_id)
    except Exception as exc:  # pragma: no cover - final API safety net
        raise HTTPException(status_code=500, detail=str(exc)) from exc

