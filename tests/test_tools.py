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