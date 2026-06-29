"""Async chat session — uses g4f.client.AsyncClient (modern API)."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Optional

from gpt4free.providers import (
    NO_AUTH_PROVIDERS,
    PROVIDER_ORDER,
    PROXY_REQUIRED_PROVIDERS,
    WORKING_PROVIDERS,
    get_provider_class,
)


try:
    from g4f.client import AsyncClient
except ImportError:
    AsyncClient = None

try:
    import g4f
    from g4f.Provider import Custom as CustomProvider
except ImportError:
    g4f = None
    CustomProvider = None
    
MAX_FALLBACK_ATTEMPTS: int = 4
PROXY_ENV_VAR: str = "G4F_PROXY"

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


def fallback_chain(primary_provider: str, primary_model: str) -> list[tuple[str, str]]:
    """Build an ordered (provider, model) chain to try."""
    chain: list[tuple[str, str]] = [(primary_provider, primary_model)]
    seen: set[str] = {primary_provider}

    ordered_candidates = [p for p in PROVIDER_ORDER if p in NO_AUTH_PROVIDERS] + \
                         [p for p in PROVIDER_ORDER if p not in NO_AUTH_PROVIDERS]

    for name in ordered_candidates:
        if len(chain) >= MAX_FALLBACK_ATTEMPTS:
            break
        if name in seen:
            continue
        models = WORKING_PROVIDERS.get(name)
        if not models:
            continue
        chain.append((name, models[0][0]))
        seen.add(name)

    return chain


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

    # streaming 

    async def ask_stream(self) -> AsyncIterator[str]:
        """
        Yield text chunks using g4f.client.AsyncClient (modern streaming API).

        Falls back to legacy g4f.ChatCompletion.create if AsyncClient fails.
        """
        from g4f.client import AsyncClient  # type: ignore[import]

        provider_cls = get_provider_class(self.provider)

        try:
            client = AsyncClient(provider=provider_cls)
            stream = client.chat.completions.stream(
                model=self.model,
                messages=self._payload(),
            )
            # stream is an async iterable, not a context manager
            async for chunk in stream:
                text = _extract_chunk(chunk)
                if text:
                    yield text
        except Exception as primary_exc:  # noqa: BLE001
            # Fallback to legacy synchronous API in a thread
            yield await self._legacy_fallback(str(primary_exc))

    async def _legacy_fallback(self, reason: str) -> str:
        """
        Try legacy g4f.ChatCompletion.create when AsyncClient fails.
        Returns the full response as one string (no streaming).
        """
        import g4f  # type: ignore[import]

        provider_cls = get_provider_class(self.provider)
        try:
            result = await asyncio.to_thread(
                g4f.ChatCompletion.create,
                model=self.model,
                messages=self._payload(),
                provider=provider_cls,
                stream=False,
            )
            # result may be str or object
            if isinstance(result, str):
                return result
            content = getattr(result, "choices", None)
            if content:
                return str(content[0].message.content)
            return str(result)
        except Exception as exc:  # noqa: BLE001
            return f"[error] {exc}\n(primary: {reason})"

    # one-shot 

    async def ask_once(self) -> str:
        """Return the full response without streaming."""
        from g4f.client import AsyncClient  # type: ignore[import]

        provider_cls = get_provider_class(self.provider)
        try:
            client = AsyncClient(provider=provider_cls)
            response = await client.chat.completions.create(
                model=self.model,
                messages=self._payload(),
            )
            return str(response.choices[0].message.content)
        except Exception as exc:  # noqa: BLE001
            # Fallback
            import g4f  # type: ignore[import]
            try:
                result = await asyncio.to_thread(
                    g4f.ChatCompletion.create,
                    model=self.model,
                    messages=self._payload(),
                    provider=provider_cls,
                    stream=False,
                )
                return str(result)
            except Exception as exc2:  # noqa: BLE001
                return f"[error] {exc2}"