"""Async chat session — uses g4f.client.AsyncClient (modern API)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Optional

from gpt4free.providers import get_provider_class


@dataclass
class Message:
    """A single conversation message."""

    role: str    # "user" | "assistant" | "system"
    content: str


def _extract_chunk(chunk: object) -> str:
    """
    Normalise a streaming chunk to a plain string.

    g4f can return:
      - str  (old-style / Blackbox)
      - ChatCompletionChunk  with .choices[0].delta.content  (new AsyncClient)
      - object with .content attribute
    """
    if isinstance(chunk, str):
        return chunk

    # New-style: chunk.choices[0].delta.content
    try:
        choices = getattr(chunk, "choices", None)
        if choices:
            delta = getattr(choices[0], "delta", None)
            if delta is not None:
                content = getattr(delta, "content", None)
                if content:
                    return str(content)
    except (IndexError, AttributeError):
        pass

    # Fallback: .content attribute
    content = getattr(chunk, "content", None)
    if content:
        return str(content)

    return ""


@dataclass
class ChatSession:
    """Stateful conversation session tied to a provider + model pair."""

    provider: str
    model: str
    messages: list[Message] = field(default_factory=list)

    def _payload(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def push_user(self, text: str) -> None:
        self.messages.append(Message("user", text))

    def push_assistant(self, text: str) -> None:
        self.messages.append(Message("assistant", text))

    def clear(self) -> None:
        self.messages.clear()