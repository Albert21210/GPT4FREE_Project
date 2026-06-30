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