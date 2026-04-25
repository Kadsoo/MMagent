from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.agent.memory import SessionStore
from app.agent.runtime import AgentRuntime
from app.schemas.chat import ChatRequest, ChatResponse, HealthResponse
from app.schemas.conversation import ConversationDetail, ConversationSummary
from app.schemas.tool import ToolSpec
from app.services.todo_service import TodoService
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
async def list_todos(
    request: Request,
    user_id: str | None = Query(default=None, min_length=2, max_length=64),
) -> list[str]:
    todo_service: TodoService | None = getattr(request.app.state, "todo_service", None)
    if todo_service:
        return todo_service.list_text_items(user_id=user_id)
    todo_store: TodoStore = request.app.state.todo_store
    return todo_store.list_items()


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    request: Request,
    user_id: str = Query(..., min_length=2, max_length=64),
) -> list[ConversationSummary]:
    sessions: SessionStore = request.app.state.sessions
    return sessions.list_conversations(user_id=user_id)


@router.get("/conversations/{session_id}", response_model=ConversationDetail)
async def get_conversation_detail(
    session_id: str,
    request: Request,
    user_id: str = Query(..., min_length=2, max_length=64),
) -> ConversationDetail:
    sessions: SessionStore = request.app.state.sessions
    detail = sessions.get_conversation_detail(user_id=user_id, session_id=session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return detail


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    runtime: AgentRuntime = request.app.state.runtime
    try:
        return await runtime.run(
            payload.message,
            user_id=payload.user_id,
            session_id=payload.session_id,
        )
    except Exception as exc:  # pragma: no cover - final API safety net
        raise HTTPException(status_code=500, detail=str(exc)) from exc
