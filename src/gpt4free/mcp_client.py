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