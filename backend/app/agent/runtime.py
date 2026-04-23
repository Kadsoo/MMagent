from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from app.agent.memory import SessionStore
from app.agent.prompts import build_system_prompt
from app.llm.base import BaseLLMAdapter
from app.schemas.chat import ChatResponse
from app.schemas.protocol import AgentMessage, FinalAnswer, ToolCall, ToolResult, TraceStep
from app.tools.registry import ToolRegistry


logger = logging.getLogger(__name__)


class AgentRuntime:
    def __init__(
        self,
        llm: BaseLLMAdapter,
        registry: ToolRegistry,
        sessions: SessionStore,
        max_steps: int = 6,
    ) -> None:
        self.llm = llm
        self.registry = registry
        self.sessions = sessions
        self.max_steps = max_steps

    async def run(self, user_input: str, session_id: str | None = None) -> ChatResponse:
        memory = self.sessions.get_or_create(session_id)
        self._ensure_system_message(memory.messages)
        memory.add_message("user", user_input)

        run_trace: list[TraceStep] = []
        final_answer = ""

        for step_no in range(1, self.max_steps + 1):
            raw_output = await self.llm.generate(
                messages=memory.messages,
                tools=self.registry.list_tools(),
            )
            memory.add_message("assistant", raw_output)
            trace_step = TraceStep(step=step_no, model_output=raw_output)

            try:
                decision = self._parse_model_output(raw_output)
                trace_step.parsed_output = decision.model_dump()
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                trace_step.error = f"Failed to parse model output: {exc}"
                final = FinalAnswer(
                    answer=(
                        "The model returned invalid JSON. "
                        "Please try again or switch to the mock adapter."
                    )
                )
                trace_step.final_answer = final
                final_answer = final.answer
                run_trace.append(trace_step)
                break

            if isinstance(decision, ToolCall):
                trace_step.tool_call = decision
                tool_result = await self._execute_tool(decision)
                trace_step.tool_result = tool_result
                memory.add_message(
                    "tool",
                    json.dumps(tool_result.model_dump(), ensure_ascii=False),
                    name=tool_result.tool_name,
                )
                run_trace.append(trace_step)
                if tool_result.status == "error":
                    logger.warning("Tool execution failed: %s", tool_result.error)
                continue

            if isinstance(decision, FinalAnswer):
                trace_step.final_answer = decision
                final_answer = decision.answer
                run_trace.append(trace_step)
                break

        if not final_answer:
            final = FinalAnswer(
                answer=(
                    "I reached the maximum reasoning steps before producing a final "
                    "answer. Please narrow the request or increase MAX_AGENT_STEPS."
                )
            )
            raw_final = json.dumps(final.model_dump(), ensure_ascii=False)
            memory.add_message("assistant", raw_final)
            run_trace.append(
                TraceStep(
                    step=len(run_trace) + 1,
                    model_output=raw_final,
                    parsed_output=final.model_dump(),
                    final_answer=final,
                )
            )
            final_answer = final.answer

        memory.extend_trace(run_trace)
        return ChatResponse(
            session_id=memory.session_id,
            final_answer=final_answer,
            trace=run_trace,
            messages=memory.messages,
        )

    def _ensure_system_message(self, messages: list[AgentMessage]) -> None:
        if messages and messages[0].role == "system":
            return
        system_prompt = build_system_prompt(self.registry.list_tools())
        messages.insert(0, AgentMessage(role="system", content=system_prompt))

    async def _execute_tool(self, tool_call: ToolCall) -> ToolResult:
        try:
            result = await self.registry.execute(tool_call.tool_name, tool_call.arguments)
            return ToolResult(
                tool_name=tool_call.tool_name,
                status="success",
                result=result,
            )
        except Exception as exc:
            return ToolResult(
                tool_name=tool_call.tool_name,
                status="error",
                error=str(exc),
            )

    @staticmethod
    def _parse_model_output(raw_output: str) -> ToolCall | FinalAnswer:
        content = raw_output.strip()
        if content.startswith("```"):
            lines = [line for line in content.splitlines() if not line.startswith("```")]
            content = "\n".join(lines).strip()

        payload: dict[str, Any] = json.loads(content)
        output_type = payload.get("type")
        if output_type == "tool_call":
            return ToolCall.model_validate(payload)
        if output_type == "final_answer":
            return FinalAnswer.model_validate(payload)
        raise ValueError(f"Unknown agent output type: {output_type}")

