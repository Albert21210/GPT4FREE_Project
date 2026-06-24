"""Tests for ChatSession (mocked g4f — no network)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gpt4free.chat import ChatSession, Message, _extract_chunk


# _extract_chunk

def test_extract_chunk_plain_string() -> None:
    assert _extract_chunk("hello") == "hello"


def test_extract_chunk_empty_string() -> None:
    assert _extract_chunk("") == ""
    

def test_extract_chunk_new_style_object() -> None:
    """Simulate chunk.choices[0].delta.content (modern g4f AsyncClient)."""
    delta = MagicMock()
    delta.content = "world"
    choice = MagicMock()
    choice.delta = delta
    chunk = MagicMock()
    chunk.choices = [choice]
    assert _extract_chunk(chunk) == "world"
    

def test_extract_chunk_none_delta_content() -> None:
    """None content should return empty string."""
    delta = MagicMock()
    delta.content = None
    choice = MagicMock()
    choice.delta = delta
    chunk = MagicMock()
    chunk.choices = [choice]
    assert _extract_chunk(chunk) == ""


def test_extract_chunk_content_attribute_fallback() -> None:
    """Object with .content but no .choices should use fallback."""
    obj = MagicMock(spec=["content"])
    obj.content = "fallback"
    # No choices attribute → AttributeError caught → fallback path
    assert _extract_chunk(obj) == "fallback"
    

# ChatSession 

def test_session_push_user() -> None:
    s = ChatSession(provider="Blackbox", model="gpt-4o")
    s.push_user("hi")
    assert s.messages[-1] == Message("user", "hi")


def test_session_push_assistant() -> None:
    s = ChatSession(provider="Blackbox", model="gpt-4o")
    s.push_assistant("hello")
    assert s.messages[-1] == Message("assistant", "hello")
    

def test_session_clear() -> None:
    s = ChatSession(provider="Blackbox", model="gpt-4o")
    s.push_user("a")
    s.push_assistant("b")
    s.clear()
    assert s.messages == []


def test_session_payload() -> None:
    s = ChatSession(provider="Blackbox", model="gpt-4o")
    s.push_user("q")
    s.push_assistant("a")
    payload = s._payload()
    assert payload == [
        {"role": "user", "content": "q"},
        {"role": "assistant", "content": "a"},
    ]