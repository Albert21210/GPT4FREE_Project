"""Wires configured tools (built-in local skills + MCP servers from AppConfig)
into a single live ToolRegistry, for both the CLI and the TUI.
"""

from __future__ import annotations

from contextlib import AsyncExitStack
from typing import Callable, Optional

from gpt4free.config import AppConfig
from gpt4free.mcp_client import MCP_AVAILABLE, connect_mcp_stdio
from gpt4free.skills import build_default_registry
from gpt4free.tools import ToolRegistry

ErrorCallback = Callable[[str, str], None]


async def build_tool_registry(
    cfg: AppConfig,
    stack: AsyncExitStack,
    on_error: Optional[ErrorCallback] = None,
) -> ToolRegistry:
    """Build a ToolRegistry with built-in skills plus every *enabled* MCP
    server from `cfg.mcp_servers`, connected and ready to call.

    `stack` must be kept open for as long as the returned registry is used —
    it owns the MCP servers' subprocess connections. A server that fails to
    connect (bad command, crashes on startup, etc.) is skipped rather than
    aborting the whole registry; `on_error(server_name, message)` is called
    for each failure if provided.
    """
    registry = build_default_registry() if cfg.builtin_tools_enabled else ToolRegistry()

    for name, server in cfg.mcp_servers.items():
        if not server.get("enabled", True):
            continue

        if not MCP_AVAILABLE:
            if on_error:
                on_error(name, "the 'mcp' package is not installed (pip install mcp)")
            continue

        try:
            source = await stack.enter_async_context(
                connect_mcp_stdio(
                    server["command"],
                    server.get("args") or [],
                    env=server.get("env") or None,
                    server_name=name,
                )
            )
            source.register_into(registry)
        except Exception as exc:  # noqa: BLE001
            if on_error:
                on_error(name, str(exc))

    return registry
