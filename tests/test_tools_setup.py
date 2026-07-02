"""Tests for gpt4free.tools_setup.build_tool_registry."""

from __future__ import annotations

from contextlib import AsyncExitStack

import pytest

from gpt4free.config import AppConfig
from gpt4free.tools_setup import build_tool_registry


@pytest.mark.asyncio
async def test_builtin_tools_registered_by_default() -> None:
    cfg = AppConfig()
    async with AsyncExitStack() as stack:
        registry = await build_tool_registry(cfg, stack)
    names = {t.name for t in registry.list_tools()}
    assert "calculator" in names
    assert "current_datetime" in names


@pytest.mark.asyncio
async def test_builtin_tools_disabled_gives_empty_registry() -> None:
    cfg = AppConfig(builtin_tools_enabled=False)
    async with AsyncExitStack() as stack:
        registry = await build_tool_registry(cfg, stack)
    assert len(registry) == 0


@pytest.mark.asyncio
async def test_disabled_mcp_server_is_skipped() -> None:
    cfg = AppConfig(builtin_tools_enabled=False)
    cfg.add_mcp_server("dummy", command="python", args=["nope.py"], enabled=False)
    async with AsyncExitStack() as stack:
        registry = await build_tool_registry(cfg, stack)
    assert len(registry) == 0


@pytest.mark.asyncio
async def test_broken_mcp_server_reports_error_but_does_not_raise() -> None:
    cfg = AppConfig(builtin_tools_enabled=False)
    cfg.add_mcp_server("broken", command="this-command-does-not-exist-xyz")

    errors: list[tuple[str, str]] = []
    async with AsyncExitStack() as stack:
        registry = await build_tool_registry(cfg, stack, on_error=lambda name, msg: errors.append((name, msg)))

    assert len(registry) == 0
    assert len(errors) == 1
    assert errors[0][0] == "broken"


@pytest.mark.asyncio
async def test_real_mcp_server_gets_registered(tmp_path) -> None:
    """End-to-end: connect to the real dummy MCP server fixture and confirm
    its tools land in the registry alongside the built-ins."""
    import sys
    from pathlib import Path

    from gpt4free.mcp_client import MCP_AVAILABLE

    if not MCP_AVAILABLE:
        pytest.skip("'mcp' package not installed")

    fixture = str(Path(__file__).parent / "fixtures" / "dummy_mcp_server.py")
    cfg = AppConfig(builtin_tools_enabled=True)
    cfg.add_mcp_server("dummy", command=sys.executable, args=[fixture])

    async with AsyncExitStack() as stack:
        registry = await build_tool_registry(cfg, stack)
        names = {t.name for t in registry.list_tools()}
        assert "calculator" in names  # built-in still present
        assert "dummy.add" in names
        assert "dummy.greet" in names
