from __future__ import annotations

import json
import re
from collections.abc import Sequence
from typing import Any

from app.llm.base import BaseLLMAdapter
from app.schemas.protocol import AgentMessage
from app.schemas.tool import ToolSpec


class MockLLMAdapter(BaseLLMAdapter):
    """Rule-based local adapter that demonstrates the Agent loop without an API key."""

    async def generate(
        self,
        messages: Sequence[AgentMessage],
        tools: Sequence[ToolSpec],
    ) -> str:
        user_message = self._latest_user_message(messages)
        tool_results = self._tool_results(messages)
        called_tools = {item.get("tool_name") for item in tool_results}
        lowered = user_message.lower()

        if self._asks_todo_add(lowered) and "todo_add" not in called_tools:
            return self._json_tool_call(
                "todo_add",
                {"item": self._extract_todo_item(user_message)},
                "The user wants to add a todo item.",
            )

        if self._asks_todo_delete(lowered) and "todo_delete" not in called_tools:
            return self._json_tool_call(
                "todo_delete",
                {"index": self._extract_first_int(user_message, default=1)},
                "The user wants to delete a todo item.",
            )

        if self._asks_todo_list(lowered) and "todo_list" not in called_tools:
            return self._json_tool_call(
                "todo_list",
                {},
                "The user wants to inspect current todos.",
            )

        if self._asks_weather(lowered) and "get_weather" not in called_tools:
            return self._json_tool_call(
                "get_weather",
                {"city": self._extract_city(user_message)},
                "Weather is external context, so call get_weather first.",
            )

        if self._asks_time(lowered) and "get_time" not in called_tools:
            return self._json_tool_call(
                "get_time",
                {"city": self._extract_city(user_message)},
                "Current time should be fetched from the time tool.",
            )

        if self._asks_calculation(lowered) and "calculator" not in called_tools:
            return self._json_tool_call(
                "calculator",
                {"expression": self._extract_expression(user_message)},
                "The request contains arithmetic, so use the calculator.",
            )

        if self._asks_docs(lowered) and "search_docs" not in called_tools:
            return self._json_tool_call(
                "search_docs",
                {"query": user_message},
                "The user asks about project knowledge, so search local docs.",
            )

        if self._asks_web_search(lowered) and "web_search" not in called_tools:
            return self._json_tool_call(
                "web_search",
                {"query": self._extract_web_query(user_message), "max_results": 5},
                "The user asks for internet information, so use web_search.",
            )

        if self._asks_status(lowered) and "get_system_status" not in called_tools:
            return self._json_tool_call(
                "get_system_status",
                {},
                "System status is tool-provided runtime metadata.",
            )

        return json.dumps(
            {
                "type": "final_answer",
                "answer": self._compose_answer(user_message, tool_results),
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _json_tool_call(tool_name: str, arguments: dict[str, Any], thought: str) -> str:
        return json.dumps(
            {
                "type": "tool_call",
                "tool_name": tool_name,
                "arguments": arguments,
                "thought": thought,
            },
            ensure_ascii=False,
        )

    @staticmethod
    def _latest_user_message(messages: Sequence[AgentMessage]) -> str:
        for message in reversed(messages):
            if message.role == "user":
                return message.content
        return ""

    @staticmethod
    def _tool_results(messages: Sequence[AgentMessage]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for message in messages:
            if message.role != "tool":
                continue
            try:
                results.append(json.loads(message.content))
            except json.JSONDecodeError:
                continue
        return results

    @staticmethod
    def _has_chinese(text: str) -> bool:
        return bool(re.search(r"[\u4e00-\u9fff]", text))

    @staticmethod
    def _asks_weather(text: str) -> bool:
        return any(token in text for token in ["weather", "temperature", "\u5929\u6c14", "\u6c14\u6e29"])

    @staticmethod
    def _asks_time(text: str) -> bool:
        return any(token in text for token in ["time", "clock", "\u51e0\u70b9", "\u65f6\u95f4"])

    @staticmethod
    def _asks_calculation(text: str) -> bool:
        if any(token in text for token in ["calculate", "calculator", "\u8ba1\u7b97"]):
            return True
        return bool(re.search(r"\d+\s*[\+\-\*/]\s*\d+", text))

    @staticmethod
    def _asks_docs(text: str) -> bool:
        return any(
            token in text
            for token in ["doc", "docs", "knowledge", "readme", "\u6587\u6863", "\u77e5\u8bc6\u5e93"]
        )

    @staticmethod
    def _asks_web_search(text: str) -> bool:
        return any(
            token in text
            for token in [
                "web search",
                "search web",
                "internet",
                "online",
                "look up online",
                "\u7f51\u7edc\u67e5\u8be2",
                "\u7f51\u7edc\u641c\u7d22",
                "\u7f51\u4e0a\u67e5",
                "\u641c\u7d22\u7f51\u7edc",
            ]
        )

    @staticmethod
    def _asks_todo_add(text: str) -> bool:
        return any(token in text for token in ["add todo", "todo add", "\u6dfb\u52a0\u5f85\u529e", "\u65b0\u589e\u5f85\u529e"])

    @staticmethod
    def _asks_todo_delete(text: str) -> bool:
        return any(token in text for token in ["delete todo", "remove todo", "todo delete", "\u5220\u9664\u5f85\u529e"])

    @staticmethod
    def _asks_todo_list(text: str) -> bool:
        return any(token in text for token in ["list todo", "todos", "\u5f85\u529e\u5217\u8868", "\u5f85\u529e"])

    @staticmethod
    def _asks_status(text: str) -> bool:
        return any(token in text for token in ["system status", "health", "\u7cfb\u7edf\u72b6\u6001"])

    @staticmethod
    def _extract_first_int(text: str, default: int) -> int:
        match = re.search(r"\d+", text)
        return int(match.group(0)) if match else default

    @staticmethod
    def _extract_expression(text: str) -> str:
        matches = re.findall(r"[0-9\.\s\+\-\*/\(\)]+", text)
        candidates = [item.strip() for item in matches if re.search(r"\d", item)]
        return max(candidates, key=len) if candidates else "0"

    @staticmethod
    def _extract_todo_item(text: str) -> str:
        patterns = [
            r"(?:add todo|todo add)\s*[:：]?\s*(.+)",
            r"(?:\u6dfb\u52a0\u5f85\u529e|\u65b0\u589e\u5f85\u529e)\s*[:：]?\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return text.strip()

    @staticmethod
    def _extract_web_query(text: str) -> str:
        patterns = [
            r"(?:web search|search web|look up online|internet search)\s*[:：]?\s*(.+)",
            r"(?:\u7f51\u7edc\u67e5\u8be2|\u7f51\u7edc\u641c\u7d22|\u7f51\u4e0a\u67e5)\s*[:：]?\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match and match.group(1).strip():
                return match.group(1).strip()
        return text.strip()

    @staticmethod
    def _extract_city(text: str) -> str:
        city_aliases = {
            "nanjing": "Nanjing",
            "\u5357\u4eac": "Nanjing",
            "beijing": "Beijing",
            "\u5317\u4eac": "Beijing",
            "shanghai": "Shanghai",
            "\u4e0a\u6d77": "Shanghai",
            "shenzhen": "Shenzhen",
            "\u6df1\u5733": "Shenzhen",
            "hangzhou": "Hangzhou",
            "\u676d\u5dde": "Hangzhou",
            "tokyo": "Tokyo",
            "\u4e1c\u4eac": "Tokyo",
            "new york": "New York",
            "\u7ebd\u7ea6": "New York",
        }
        lowered = text.lower()
        for alias, city in city_aliases.items():
            if alias in lowered or alias in text:
                return city
        return "Nanjing"

    def _compose_answer(self, user_message: str, tool_results: list[dict[str, Any]]) -> str:
        if not tool_results:
            if self._has_chinese(user_message):
                return "我可以通过 JSON tool calling 调用天气、时间、计算器、知识库、网络查询和待办工具。请给我一个具体任务。"
            return "I can use JSON tool calling for weather, time, calculator, docs, web search, and todos. Give me a concrete task."

        chinese = self._has_chinese(user_message)
        lines: list[str] = []
        for item in tool_results:
            tool_name = item.get("tool_name", "tool")
            status = item.get("status")
            result = item.get("result")
            error = item.get("error")
            if status == "error":
                lines.append(f"{tool_name} failed: {error}")
                continue
            lines.append(self._summarize_tool_result(tool_name, result, chinese))

        return "；".join(lines) if chinese else " ".join(lines)

    @staticmethod
    def _summarize_tool_result(tool_name: str, result: Any, chinese: bool) -> str:
        if tool_name == "get_weather" and isinstance(result, dict):
            if chinese:
                return f"{result['city']} 当前天气为 {result['condition']}，气温 {result['temperature']}。"
            return f"The weather in {result['city']} is {result['condition']} and {result['temperature']}."

        if tool_name == "get_time" and isinstance(result, dict):
            if chinese:
                return f"{result['city_or_timezone']} 当前时间是 {result['local_time']}（{result['timezone']}）。"
            return f"The current time in {result['city_or_timezone']} is {result['local_time']} ({result['timezone']})."

        if tool_name == "calculator" and isinstance(result, dict):
            if chinese:
                return f"计算结果：{result['expression']} = {result['value']}。"
            return f"The calculation result is {result['expression']} = {result['value']}."

        if tool_name == "search_docs" and isinstance(result, dict):
            summary = result.get("summary", "No summary.")
            return f"知识库检索结果：{summary}" if chinese else f"Docs result: {summary}"

        if tool_name == "web_search" and isinstance(result, dict):
            answer = result.get("answer") or "No direct answer was returned."
            first_result = (result.get("results") or [{}])[0]
            url = result.get("source_url") or first_result.get("url") or result.get("search_page_url")
            if chinese:
                return f"网络查询结果：{answer} 来源：{url}"
            return f"Web search result: {answer} Source: {url}"

        if tool_name == "todo_add" and isinstance(result, dict):
            if chinese:
                return f"已添加待办 #{result['index']}：{result['item']}。"
            return f"Added todo #{result['index']}: {result['item']}."

        if tool_name == "todo_list" and isinstance(result, dict):
            items = result.get("items", [])
            if not items:
                return "当前没有待办事项。" if chinese else "There are no todos yet."
            rendered = ", ".join(
                f"{idx + 1}. {item.get('item', item) if isinstance(item, dict) else item}"
                for idx, item in enumerate(items)
            )
            return f"当前待办：{rendered}。" if chinese else f"Current todos: {rendered}."

        if tool_name == "todo_delete" and isinstance(result, dict):
            if chinese:
                return f"已删除待办 #{result['deleted_index']}：{result['deleted_item']}。"
            return f"Deleted todo #{result['deleted_index']}: {result['deleted_item']}."

        if tool_name == "get_system_status" and isinstance(result, dict):
            if chinese:
                return f"系统状态正常：{result['registered_tools']} 个工具已注册，LLM adapter 为 {result['llm_mode']}。"
            return f"System is healthy: {result['registered_tools']} tools registered, LLM adapter is {result['llm_mode']}."

        return json.dumps(result, ensure_ascii=False)
