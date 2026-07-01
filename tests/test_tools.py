"""Tests for the tool/skill registry (gpt4free.tools) and ChatSession.ask_with_tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gpt4free.chat import ChatSession
from gpt4free.tools import Tool, ToolRegistry, parse_tool_arguments


# parse_tool_arguments

def test_parse_tool_arguments_valid_json() -> None:
    assert parse_tool_arguments('{"city": "Helsinki"}') == {"city": "Helsinki"}


def test_parse_tool_arguments_empty() -> None:
    assert parse_tool_arguments("") == {}
    assert parse_tool_arguments(None) == {}


def test_parse_tool_arguments_malformed() -> None:
    assert parse_tool_arguments("{not json") == {}


def test_parse_tool_arguments_already_dict() -> None:
    assert parse_tool_arguments({"a": 1}) == {"a": 1}


def test_parse_tool_arguments_non_dict_json() -> None:
    assert parse_tool_arguments("[1, 2, 3]") == {}
    

# Tool / ToolRegistry

def test_tool_to_openai_schema() -> None:
    tool = Tool(name="ping", description="Replies pong", handler=lambda: "pong")
    schema = tool.to_openai_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "ping"
    assert schema["function"]["description"] == "Replies pong"
    
    
@pytest.mark.asyncio
async def test_tool_call_sync_handler() -> None:
    tool = Tool(name="add", description="adds two numbers", handler=lambda a, b: a + b)
    result = await tool.call(a=2, b=3)
    assert result == "5"  # non-str results get json-encoded


@pytest.mark.asyncio
async def test_tool_call_async_handler() -> None:
    async def handler(city: str) -> str:
        return f"Sunny in {city}"

    tool = Tool(name="weather", description="weather lookup", handler=handler)
    result = await tool.call(city="Helsinki")
    assert result == "Sunny in Helsinki"


@pytest.mark.asyncio
async def test_tool_call_no_handler_returns_error() -> None:
    tool = Tool(name="broken", description="no handler")
    result = await tool.call()
    assert "error" in result


def test_registry_skill_decorator() -> None:
    registry = ToolRegistry()

    @registry.skill("echo", "echoes input", {"type": "object", "properties": {"text": {"type": "string"}}})
    def echo(text: str) -> str:
        return text

    assert "echo" in registry
    assert len(registry) == 1
    assert registry.get("echo") is not None


def test_registry_to_openai_schema_multiple_tools() -> None:
    registry = ToolRegistry()
    registry.register(Tool(name="a", description="A", handler=lambda: "a"))
    registry.register(Tool(name="b", description="B", handler=lambda: "b"))
    schema = registry.to_openai_schema()
    assert len(schema) == 2
    assert {s["function"]["name"] for s in schema} == {"a", "b"}
    
    
@pytest.mark.asyncio
async def test_registry_execute_unknown_tool() -> None:
    registry = ToolRegistry()
    result = await registry.execute("nope", {})
    assert "error" in result


@pytest.mark.asyncio
async def test_registry_execute_known_tool() -> None:
    registry = ToolRegistry()
    registry.register(Tool(name="double", description="doubles a number", handler=lambda n: n * 2))
    result = await registry.execute("double", {"n": 4})
    assert result == "8"