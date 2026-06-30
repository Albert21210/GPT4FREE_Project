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


@dataclass
class MCPToolSource:
    """A live connection to one MCP server, with its tools discovered and wrapped."""

    server_name: str
    session: "ClientSession"
    tools: list[Tool] = field(default_factory=list)

    async def discover(self) -> list[Tool]:
        """List the server's tools, wrap each as a gpt4free `Tool`, cache and return them."""
        listing = await self.session.list_tools()
        self.tools = [self._wrap(t) for t in listing.tools]
        return self.tools

    def _wrap(self, mcp_tool: Any) -> Tool:
        # Prefix with the server name to avoid collisions when multiple MCP
        # servers (or local skills) expose tools with the same short name.
        qualified_name = f"{self.server_name}.{mcp_tool.name}"

        async def handler(**kwargs: Any) -> str:
            result = await self.session.call_tool(mcp_tool.name, arguments=kwargs)
            return _extract_text(result)

        return Tool(
            name=qualified_name,
            description=mcp_tool.description or f"Tool '{mcp_tool.name}' from MCP server '{self.server_name}'",
            parameters=mcp_tool.inputSchema or {"type": "object", "properties": {}},
            handler=handler,
        )

    def register_into(self, registry: ToolRegistry) -> list[Tool]:
        """Register all discovered tools into `registry`. Call discover() first
        (connect_mcp_stdio/connect_mcp_http already do this for you)."""
        for tool in self.tools:
            registry.register(tool)
        return self.tools
    
    
@asynccontextmanager
async def connect_mcp_stdio(
    command: str,
    args: Optional[list[str]] = None,
    env: Optional[dict[str, str]] = None,
    server_name: Optional[str] = None,
) -> AsyncIterator[MCPToolSource]:
    """
    Launch a local MCP server as a subprocess and connect to it over stdio.

    `command`/`args` are exactly what you'd type to run the server yourself,
    e.g. command="python", args=["my_mcp_server.py"], or
    command="npx", args=["-y", "@some/mcp-server"].
    """
    if not MCP_AVAILABLE:
        raise MCPNotInstalledError()

    params = StdioServerParameters(command=command, args=args or [], env=env)
    name = server_name or command

    async with AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        source = MCPToolSource(server_name=name, session=session)
        await source.discover()
        yield source