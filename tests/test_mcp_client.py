"""Integration tests for gpt4free.mcp_client.

These spin up a real (tiny) MCP server as a subprocess over stdio and talk
to it over the actual MCP protocol — no mocks for the MCP transport itself.
The dummy server lives at tests/fixtures/dummy_mcp_server.py.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from gpt4free.mcp_client import MCP_AVAILABLE, connect_mcp_stdio
from gpt4free.tools import ToolRegistry

pytestmark = pytest.mark.skipif(not MCP_AVAILABLE, reason="'mcp' package not installed")

FIXTURE_SERVER = str(Path(__file__).parent / "fixtures" / "dummy_mcp_server.py")


@pytest.mark.asyncio
async def test_connect_and_discover_tools() -> None:
    async with connect_mcp_stdio(sys.executable, [FIXTURE_SERVER], server_name="dummy") as source:
        names = {t.name for t in source.tools}
        assert names == {"dummy.add", "dummy.greet"}
        
        
@pytest.mark.asyncio
async def test_register_into_populates_registry() -> None:
    registry = ToolRegistry()
    async with connect_mcp_stdio(sys.executable, [FIXTURE_SERVER], server_name="dummy") as source:
        source.register_into(registry)

    assert len(registry) == 2
    assert "dummy.add" in registry
    assert "dummy.greet" in registry