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