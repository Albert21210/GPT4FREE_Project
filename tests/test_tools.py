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


# ChatSession.ask_with_tools

@pytest.mark.asyncio
async def test_ask_with_tools_no_tools_falls_back_to_ask_once() -> None:
    mock_message = MagicMock()
    mock_message.content = "plain answer"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("gpt4free.chat.AsyncClient", return_value=mock_client), \
         patch("gpt4free.chat.get_provider_class", return_value=MagicMock()):
        s = ChatSession(provider="PollinationsAI", model="openai", auto_fallback=False)
        s.push_user("hi")
        result = await s.ask_with_tools()

    assert result == "plain answer"


@pytest.mark.asyncio
async def test_ask_with_tools_executes_tool_then_returns_final_answer() -> None:
    registry = ToolRegistry()

    @registry.skill("get_weather", "weather lookup",
                     {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]})
    async def get_weather(city: str) -> str:
        return f"Sunny in {city}"

    # First model call: requests a tool call.
    tool_call = MagicMock()
    tool_call.id = "call_1"
    tool_call.function.name = "get_weather"
    tool_call.function.arguments = '{"city": "Helsinki"}'

    first_message = MagicMock()
    first_message.tool_calls = [tool_call]
    first_message.content = None
    first_choice = MagicMock()
    first_choice.message = first_message
    first_response = MagicMock()
    first_response.choices = [first_choice]

    # Second model call: returns the final text answer.
    second_message = MagicMock()
    second_message.tool_calls = None
    second_message.content = "It's sunny in Helsinki."
    second_choice = MagicMock()
    second_choice.message = second_message
    second_response = MagicMock()
    second_response.choices = [second_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=[first_response, second_response])

    with patch("gpt4free.chat.AsyncClient", return_value=mock_client), \
         patch("gpt4free.chat.get_provider_class", return_value=MagicMock()):
        s = ChatSession(provider="PollinationsAI", model="openai", tools=registry, auto_fallback=False)
        s.push_user("What's the weather in Helsinki?")
        result = await s.ask_with_tools()

    assert result == "It's sunny in Helsinki."
    # Conversation should now contain the tool-call + tool-result messages.
    roles = [m.role for m in s.messages]
    assert "tool" in roles
    tool_msg = next(m for m in s.messages if m.role == "tool")
    assert tool_msg.content == "Sunny in Helsinki"
    assert mock_client.chat.completions.create.await_count == 2


@pytest.mark.asyncio
async def test_ask_with_tools_passes_schema_to_create() -> None:
    registry = ToolRegistry()
    registry.register(Tool(name="noop", description="does nothing", handler=lambda: "ok"))

    mock_message = MagicMock()
    mock_message.tool_calls = None
    mock_message.content = "done"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("gpt4free.chat.AsyncClient", return_value=mock_client), \
         patch("gpt4free.chat.get_provider_class", return_value=MagicMock()):
        s = ChatSession(provider="PollinationsAI", model="openai", tools=registry, auto_fallback=False)
        s.push_user("hi")
        await s.ask_with_tools()

    _, kwargs = mock_client.chat.completions.create.call_args
    assert "tools" in kwargs
    assert kwargs["tools"][0]["function"]["name"] == "noop"


@pytest.mark.asyncio
async def test_ask_with_tools_respects_max_iterations() -> None:
    """If the model keeps requesting tool calls forever, the loop should
    bail out after max_tool_iterations rather than spinning forever."""
    registry = ToolRegistry()
    registry.register(Tool(name="loop", description="loops", handler=lambda: "again"))

    tool_call = MagicMock()
    tool_call.id = "call_x"
    tool_call.function.name = "loop"
    tool_call.function.arguments = "{}"

    looping_message = MagicMock()
    looping_message.tool_calls = [tool_call]
    looping_message.content = None
    looping_choice = MagicMock()
    looping_choice.message = looping_message
    looping_response = MagicMock()
    looping_response.choices = [looping_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=looping_response)

    with patch("gpt4free.chat.AsyncClient", return_value=mock_client), \
         patch("gpt4free.chat.get_provider_class", return_value=MagicMock()):
        s = ChatSession(provider="PollinationsAI", model="openai", tools=registry,
                         auto_fallback=False, max_tool_iterations=2)
        s.push_user("loop forever")
        result = await s.ask_with_tools()

    assert "max_tool_iterations" in result
    assert mock_client.chat.completions.create.await_count == 2
