from __future__ import annotations

import json
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional

from gpt4free.tools import Tool, ToolRegistry

try:
    from mcp import ClientSession, StdioServerParameters  # type: ignore[import]
    from mcp.client.stdio import stdio_client  # type: ignore[import]
    from mcp.client.streamable_http import streamablehttp_client  # type: ignore[import]
    MCP_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised when the `mcp` package isn't installed
    ClientSession = None  # type: ignore[assignment]
    StdioServerParameters = None  # type: ignore[assignment]
    stdio_client = None  # type: ignore[assignment]
    streamablehttp_client = None  # type: ignore[assignment]
    MCP_AVAILABLE = False


class MCPNotInstalledError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "The 'mcp' package is required for MCP server integration. "
            "Install it with: pip install mcp"
        )
        
        
def _extract_text(result: Any) -> str:
    """Flatten an MCP CallToolResult into a plain string for the model."""
    if getattr(result, "isError", False):
        parts = [getattr(c, "text", str(c)) for c in getattr(result, "content", [])]
        return json.dumps({"error": " ".join(parts) or "tool call failed"})

    content = getattr(result, "content", None) or []
    texts = [t for t in (getattr(c, "text", None) for c in content) if t]
    if texts:
        return "\n".join(texts)

    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return json.dumps(structured, ensure_ascii=False, default=str)

    if content:
        # Non-text content (images, embedded resources, ...) — describe it
        # rather than silently dropping it, so the model knows something came back.
        return json.dumps([{"type": getattr(c, "type", "unknown")} for c in content], ensure_ascii=False)

    return ""