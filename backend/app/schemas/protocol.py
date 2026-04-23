from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["tool_call"] = "tool_call"
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    thought: str | None = None


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["tool_result"] = "tool_result"
    tool_name: str
    status: Literal["success", "error"]
    result: Any | None = None
    error: str | None = None


class FinalAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["final_answer"] = "final_answer"
    answer: str


class AgentMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None


class TraceStep(BaseModel):
    step: int
    model_output: str | None = None
    parsed_output: dict[str, Any] | None = None
    tool_call: ToolCall | None = None
    tool_result: ToolResult | None = None
    final_answer: FinalAnswer | None = None
    error: str | None = None

