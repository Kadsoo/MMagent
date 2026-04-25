from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from app.schemas.tool import ToolSpec
from app.tools.context import ToolContext


ToolHandler = Callable[..., Any | Awaitable[Any]]


class RegisteredTool:
    def __init__(
        self,
        name: str,
        description: str,
        args_model: type[BaseModel],
        handler: ToolHandler,
    ) -> None:
        self.name = name
        self.description = description
        self.args_model = args_model
        self.handler = handler

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name=self.name,
            description=self.description,
            input_schema=self.args_model.model_json_schema(),
        )

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext | None = None,
    ) -> Any:
        try:
            parsed_args = self.args_model.model_validate(arguments)
        except ValidationError as exc:
            raise ValueError(f"Invalid arguments for tool '{self.name}': {exc}") from exc

        signature = inspect.signature(self.handler)
        if "context" in signature.parameters or len(signature.parameters) >= 2:
            result = self.handler(parsed_args, context)
        else:
            result = self.handler(parsed_args)
        if inspect.isawaitable(result):
            return await result
        return result


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(
        self,
        name: str,
        description: str,
        args_model: type[BaseModel],
        handler: ToolHandler,
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = RegisteredTool(name, description, args_model, handler)

    def get(self, name: str) -> RegisteredTool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {name}") from exc

    def list_tools(self) -> list[ToolSpec]:
        return [tool.spec() for tool in self._tools.values()]

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: ToolContext | None = None,
    ) -> Any:
        return await self.get(name).execute(arguments, context=context)
