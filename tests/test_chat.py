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