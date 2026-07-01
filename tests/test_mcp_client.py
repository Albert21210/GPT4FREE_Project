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


@pytest.mark.asyncio
async def test_call_real_mcp_tool_add() -> None:
    registry = ToolRegistry()
    async with connect_mcp_stdio(sys.executable, [FIXTURE_SERVER], server_name="dummy") as source:
        source.register_into(registry)
        result = await registry.execute("dummy.add", {"a": 3, "b": 4})

    assert result == "7"


@pytest.mark.asyncio
async def test_call_real_mcp_tool_greet() -> None:
    registry = ToolRegistry()
    async with connect_mcp_stdio(sys.executable, [FIXTURE_SERVER], server_name="dummy") as source:
        source.register_into(registry)
        result = await registry.execute("dummy.greet", {"name": "Vitaly"})

    assert result == "Hello, Vitaly!"


@pytest.mark.asyncio
async def test_tool_schema_has_correct_parameters() -> None:
    async with connect_mcp_stdio(sys.executable, [FIXTURE_SERVER], server_name="dummy") as source:
        add_tool = next(t for t in source.tools if t.name == "dummy.add")
        schema = add_tool.to_openai_schema()

    assert schema["function"]["name"] == "dummy.add"
    props = schema["function"]["parameters"]["properties"]
    assert "a" in props and "b" in props


@pytest.mark.asyncio
async def test_end_to_end_with_chat_session_ask_with_tools() -> None:
    """Full pipeline: real MCP tool registered into a ChatSession, model call
    is mocked (no network), but the tool *execution* hits the real subprocess."""
    from unittest.mock import AsyncMock, MagicMock, patch

    from gpt4free.chat import ChatSession

    registry = ToolRegistry()
    async with connect_mcp_stdio(sys.executable, [FIXTURE_SERVER], server_name="dummy") as source:
        source.register_into(registry)

        tool_call = MagicMock()
        tool_call.id = "call_1"
        tool_call.function.name = "dummy.add"
        tool_call.function.arguments = '{"a": 10, "b": 32}'

        first_message = MagicMock()
        first_message.tool_calls = [tool_call]
        first_message.content = None
        first_response = MagicMock()
        first_response.choices = [MagicMock(message=first_message)]

        second_message = MagicMock()
        second_message.tool_calls = None
        second_message.content = "The answer is 42."
        second_response = MagicMock()
        second_response.choices = [MagicMock(message=second_message)]

        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[first_response, second_response])

        with patch("gpt4free.chat.AsyncClient", return_value=mock_client), \
             patch("gpt4free.chat.get_provider_class", return_value=MagicMock()):
            session = ChatSession(provider="PollinationsAI", model="openai", tools=registry, auto_fallback=False)
            session.push_user("What is 10 + 32?")
            answer = await session.ask_with_tools()

    assert answer == "The answer is 42."
    tool_msg = next(m for m in session.messages if m.role == "tool")
    assert tool_msg.content == "42"
