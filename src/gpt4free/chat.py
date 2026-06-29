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
from gpt4free.tools import ToolRegistry, parse_tool_arguments

try:
    from g4f.client import AsyncClient
except ImportError:  
    AsyncClient = None  

try:
    import g4f  # type: ignore[import]
    from g4f.Provider import Custom as CustomProvider  # type: ignore[import]
except ImportError:  # pragma: no cover
    g4f = None  # type: ignore[assignment]
    CustomProvider = None  # type: ignore[assignment]

MAX_FALLBACK_ATTEMPTS: int = 4
PROXY_ENV_VAR: str = "G4F_PROXY"

@dataclass
class Message:
    """A single conversation message с поддержкой вызова функций."""

    role: str    # "user" | "assistant" | "system" | "tool"
    content: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


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
                return str(content) if content else ""
    except (IndexError, AttributeError):
        pass

    # Fallback: .content attribute (only reached when chunk has no .choices)
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
    auto_fallback: bool = True

    # Proxy URL, e.g. "socks5://127.0.0.1:1080" or "http://user:pass@host:port".
    # it (Gemini/MetaAI/Grok); set force_proxy=True to route every provider
    proxy: Optional[str] = None
    force_proxy: bool = False

    tools: Optional[ToolRegistry] = None
    max_tool_iterations: int = 5

    api_keys: dict[str, str] = field(default_factory=dict)

    custom_providers: dict[str, dict] = field(default_factory=dict)

    last_provider: Optional[str] = field(default=None, init=False)
    last_model: Optional[str] = field(default=None, init=False)

    def _payload(self) -> list[dict[str, str]]:
        payload: list[dict] = []
        for m in self.messages:
            entry: dict = {"role": m.role}
            if m.content is not None:
                entry["content"] = m.content
            if m.tool_calls:
                entry["tool_calls"] = m.tool_calls
            if m.tool_call_id:
                entry["tool_call_id"] = m.tool_call_id
            if m.name:
                entry["name"] = m.name
            payload.append(entry)
        return payload

    def push_user(self, text: str) -> None:
        self.messages.append(Message("user", text))

    def push_assistant(self, text: str) -> None:
        self.messages.append(Message("assistant", text))

    def push_tool_result(self, tool_call_id: str, name: str, content: str) -> None:
        self.messages.append(Message(role="tool", content=content, tool_call_id=tool_call_id, name=name))

    def clear(self) -> None:
        self.messages.clear()

    def _chain(self) -> list[tuple[str, str]]:
        if not self.auto_fallback:
            return [(self.provider, self.model)]
        return fallback_chain(self.provider, self.model)

    def _resolved_proxy(self) -> Optional[str]:
        return self.proxy or os.environ.get(PROXY_ENV_VAR) or None

    def _resolve(self, provider_name: str) -> tuple[object, dict]:
        """Custom provider api."""
        custom = self.custom_providers.get(provider_name)
        if custom:
            extra: dict = {"base_url": custom.get("base_url")}
            key = custom.get("api_key")
            if key:
                extra["api_key"] = key
            return CustomProvider, extra

        provider_cls = get_provider_class(provider_name)
        extra = {}
        key = self.api_keys.get(provider_name)
        if key:
            extra["api_key"] = key
        return provider_cls, extra

    def _proxy_for(self, provider_name: str) -> Optional[str]:
        """Decide whether this specific provider call should go through the proxy."""
        proxy = self._resolved_proxy()
        if not proxy:
            return None
        if self.force_proxy or provider_name in PROXY_REQUIRED_PROVIDERS:
            return proxy
        return None

    async def _call_model(self, extra_kwargs: Optional[dict] = None) -> tuple[object, str, str]:
        """
        Walk the fallback chain trying AsyncClient.chat.completions.create().
        Returns (response, provider_name, model) for the first provider that
        succeeds. Raises the last exception if every provider in the chain
        fails — callers decide whether to fall back further (e.g. legacy API)
        or surface the error.
        """
        last_error: Optional[Exception] = None

        for provider_name, model in self._chain():
            provider_cls, resolve_extra = self._resolve(provider_name)
            proxy = self._proxy_for(provider_name)
            create_kwargs: dict = {"model": model, "messages": self._payload()}
            create_kwargs.update(resolve_extra)
            if proxy:
                create_kwargs["proxy"] = proxy
            if extra_kwargs:
                create_kwargs.update(extra_kwargs)
            try:
                client = AsyncClient(provider=provider_cls)
                response = await client.chat.completions.create(**create_kwargs)
                self.last_provider, self.last_model = provider_name, model
                return response, provider_name, model
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue

        raise last_error if last_error else RuntimeError("no providers available")

    # streaming 

    async def ask_stream(self) -> AsyncIterator[str]:
        """
        Yield text chunks using g4f.client.AsyncClient (modern streaming API).

        Tries each (provider, model) pair in the fallback chain in turn.
        A provider only counts as "failed" if it raises before yielding any
        chunk, so a stream that starts and then dies mid-way is not silently
        retried from scratch with a different provider.
        """
        last_error: Optional[Exception] = None

        for provider_name, model in self._chain():
            provider_cls, resolve_extra = self._resolve(provider_name)
            proxy = self._proxy_for(provider_name)
            stream_kwargs: dict = {"model": model, "messages": self._payload()}
            stream_kwargs.update(resolve_extra)
            if proxy:
                stream_kwargs["proxy"] = proxy

            yielded_any = False
            try:
                client = AsyncClient(provider=provider_cls)
                stream = client.chat.completions.stream(**stream_kwargs)
                async for chunk in stream:
                    text = _extract_chunk(chunk)
                    if text:
                        yielded_any = True
                        self.last_provider, self.last_model = provider_name, model
                        yield text
                if yielded_any:
                    return
                last_error = RuntimeError(f"{provider_name}: empty stream")
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if yielded_any:
                    # Already streamed partial content to the user — don't
                    # restart with a different provider mid-conversation.
                    return
                continue

        # Every provider in the chain failed before yielding anything.
        yield await self._legacy_fallback(str(last_error) if last_error else "unknown error")

    async def _legacy_fallback(self, reason: str) -> str:
        """
        Try legacy g4f.ChatCompletion.create across the fallback chain when
        AsyncClient fails for every provider. Returns the full response as
        one string (no streaming).
        """
        last_error = reason
        for provider_name, model in self._chain():
            provider_cls, resolve_extra = self._resolve(provider_name)
            proxy = self._proxy_for(provider_name)
            create_kwargs: dict = {
                "model": model,
                "messages": self._payload(),
                "provider": provider_cls,
                "stream": False,
            }
            create_kwargs.update(resolve_extra)
            if proxy:
                create_kwargs["proxy"] = proxy
            try:
                result = await asyncio.to_thread(g4f.ChatCompletion.create, **create_kwargs)
                self.last_provider, self.last_model = provider_name, model
                if isinstance(result, str):
                    return result
                content = getattr(result, "choices", None)
                if content:
                    return str(content[0].message.content)
                return str(result)
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                continue

        return f"[error] all providers failed (last: {last_error})"

    # one-shot

    async def ask_once(self) -> str:
        """Return the full response without streaming, walking the fallback chain."""
        last_error: Optional[Exception] = None

        for provider_name, model in self._chain():
            provider_cls, resolve_extra = self._resolve(provider_name)
            proxy = self._proxy_for(provider_name)
            create_kwargs: dict = {"model": model, "messages": self._payload()}
            create_kwargs.update(resolve_extra)
            if proxy:
                create_kwargs["proxy"] = proxy
            try:
                client = AsyncClient(provider=provider_cls)
                response = await client.chat.completions.create(**create_kwargs)
                self.last_provider, self.last_model = provider_name, model
                return str(response.choices[0].message.content)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue

        return await self._legacy_fallback(str(last_error) if last_error else "unknown error")

    # tool calling

    async def ask_with_tools(self) -> str:
        """
        Run a function-calling agent loop: ask the model, execute any tool
        calls it requests via `self.tools`, feed the results back, and repeat
        until the model returns a plain text answer (or `max_tool_iterations`
        is reached).

        Requires `self.tools` to be set; falls back to a plain `ask_once()`
        if no tools are registered.
        """
        if not self.tools or len(self.tools) == 0:
            return await self.ask_once()

        schema = self.tools.to_openai_schema()

        for _ in range(self.max_tool_iterations):
            try:
                response, _, _ = await self._call_model({"tools": schema, "tool_choice": "auto"})
            except Exception as exc:  # noqa: BLE001
                return await self._legacy_fallback(str(exc))

            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None)

            if not tool_calls:
                content = str(getattr(message, "content", "") or "")
                self.push_assistant(content)
                return content

            # Record the assistant's tool-call request, then execute each
            # tool and feed its result back as a "tool" message.
            serialised_calls = [
                {
                    "id": getattr(tc, "id", None) or f"call_{i}",
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for i, tc in enumerate(tool_calls)
            ]
            self.messages.append(Message(role="assistant", content=None, tool_calls=serialised_calls))

            for tc in serialised_calls:
                fn_name = tc["function"]["name"]
                arguments = parse_tool_arguments(tc["function"]["arguments"])
                result = await self.tools.execute(fn_name, arguments)
                self.push_tool_result(tool_call_id=tc["id"], name=fn_name, content=result)

        return "[error] reached max_tool_iterations without a final answer"
