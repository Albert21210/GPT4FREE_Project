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


@pytest.mark.asyncio
async def test_ask_once_success() -> None:
    """ask_once should return message content from AsyncClient response."""
    mock_message = MagicMock()
    mock_message.content = "pong"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("gpt4free.chat.AsyncClient", return_value=mock_client), \
         patch("gpt4free.chat.get_provider_class", return_value=MagicMock()):
        s = ChatSession(provider="Blackbox", model="gpt-4o")
        s.push_user("ping")
        result = await s.ask_once()

    assert result == "pong"


@pytest.mark.asyncio
async def test_ask_once_fallback_on_error() -> None:
    """ask_once should fall back to legacy API on AsyncClient error."""
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=Exception("AsyncClient failed")
    )

    with patch("gpt4free.chat.AsyncClient", return_value=mock_client), \
         patch("gpt4free.chat.get_provider_class", return_value=MagicMock()), \
         patch("asyncio.to_thread", new_callable=AsyncMock, return_value="legacy reply"):
        s = ChatSession(provider="Blackbox", model="gpt-4o")
        s.push_user("hi")
        result = await s.ask_once()

    assert result == "legacy reply"


# fallback_chain 

def test_fallback_chain_starts_with_primary() -> None:
    chain = fallback_chain("PollinationsAI", "openai")
    assert chain[0] == ("PollinationsAI", "openai")


def test_fallback_chain_no_duplicate_primary() -> None:
    """Primary provider should not also appear later in the chain."""
    chain = fallback_chain("Qwen", "qwen3.7-plus")
    names = [name for name, _ in chain]
    assert names.count("Qwen") == 1


def test_fallback_chain_prefers_no_auth_providers() -> None:
    """No-auth providers should be tried before auth-required ones."""
    from gpt4free.providers import NO_AUTH_PROVIDERS

    chain = fallback_chain("Grok", "grok-4")  # Grok itself needs auth
    fallback_names = [name for name, _ in chain[1:]]
    no_auth_in_chain = [n for n in fallback_names if n in NO_AUTH_PROVIDERS]
    auth_in_chain = [n for n in fallback_names if n not in NO_AUTH_PROVIDERS]
    if no_auth_in_chain and auth_in_chain:
        assert fallback_names.index(no_auth_in_chain[0]) < fallback_names.index(auth_in_chain[0])


def test_fallback_chain_respects_max_attempts() -> None:
    from gpt4free.chat import MAX_FALLBACK_ATTEMPTS

    chain = fallback_chain("PollinationsAI", "openai")
    assert len(chain) <= MAX_FALLBACK_ATTEMPTS


def test_fallback_chain_unknown_provider_still_gets_fallbacks() -> None:
    """Even a provider with no entry in WORKING_PROVIDERS gets a fallback chain."""
    chain = fallback_chain("SomeRandomProvider", "some-model")
    assert chain[0] == ("SomeRandomProvider", "some-model")
    assert len(chain) > 1