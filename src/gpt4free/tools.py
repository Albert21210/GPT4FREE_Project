from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional, Union

ToolHandler = Callable[..., Union[str, Awaitable[str], Any]]


@dataclass
class Tool:
    """A single callable tool/skill exposed to the model."""

    name: str
    description: str
    parameters: dict[str, Any] = field(
        default_factory=lambda: {"type": "object", "properties": {}}
    )
    handler: Optional[ToolHandler] = None

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
    
    async def call(self, **kwargs: Any) -> str:
        if self.handler is None:
            return json.dumps({"error": f"tool '{self.name}' has no handler"})
        result = self.handler(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, str):
            return result
        return json.dumps(result, ensure_ascii=False, default=str)
    
    
class ToolRegistry:
    """Holds the set of tools/skills available to a ChatSession."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> Tool:
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def to_openai_schema(self) -> list[dict[str, Any]]:
        return [t.to_openai_schema() for t in self._tools.values()]
    
    async def execute(self, name: str, arguments: dict[str, Any]) -> str:
        tool = self.get(name)
        if tool is None:
            return json.dumps({"error": f"unknown tool '{name}'"})
        try:
            return await tool.call(**arguments)
        except Exception as exc:  # noqa: BLE001
            return json.dumps({"error": str(exc)})
        
    
    