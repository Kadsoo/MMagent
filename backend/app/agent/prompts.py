from __future__ import annotations

import json

from app.schemas.tool import ToolSpec


def build_system_prompt(tools: list[ToolSpec]) -> str:
    tool_payload = [tool.model_dump() for tool in tools]
    return (
        "You are MMagent, a JSON Tool Calling Agent runtime demo.\n"
        "You must respond with exactly one JSON object and no markdown.\n"
        "Choose one of these protocols:\n"
        "1. Tool call: "
        '{"type":"tool_call","tool_name":"name","arguments":{},"thought":"why"}\n'
        "2. Final answer: "
        '{"type":"final_answer","answer":"answer for the user"}\n\n'
        "Use tools when external data, calculation, documents, todos, or game-state "
        "lookups are needed. After receiving tool_result messages, continue reasoning "
        "until you can answer finally. Never invent tool results.\n\n"
        "Available tools:\n"
        f"{json.dumps(tool_payload, ensure_ascii=False, indent=2)}"
    )

