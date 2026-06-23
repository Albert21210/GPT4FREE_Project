from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional


WORKING_PROVIDERS: dict[str, list[tuple[str, str]]] = {
    "PollinationsAI": [
        ("openai", "GPT-4o"),
        ("openai-large", "GPT-4o Large"),
        ("mistral", "Mistral Large"),
    ],
    "ChatGptEs": [
        ("gpt-4o", "GPT-4o"),
    ],
    "Nexra": [
        ("gpt-4o", "GPT-4o"),
        ("gpt-4", "GPT-4"),
    ],
}

PROVIDER_ORDER: list[str] = [
    "PollinationsAI",
    "ChatGptEs",
    "Nexra",
]

DEFAULT_PROVIDER: str = "PollinationsAI"
DEFAULT_MODEL: str = "openai"

PROBE_PROMPT: str = "Reply with one word: hello"
PROBE_TIMEOUT: float = 12.0

class ProviderStatus(str, Enum):
    UNKNOWN = "unknown"
    WORKING = "working"
    RATE_LIMITED = "rate_limited"
    AUTH_REQUIRED = "auth_required"
    DOWN = "down"

STATUS_EMOJI: dict[ProviderStatus, str] = {
    ProviderStatus.WORKING:       "✅",
    ProviderStatus.RATE_LIMITED:  "⚠️ ",
    ProviderStatus.AUTH_REQUIRED: "🔑",
    ProviderStatus.DOWN:          "❌",
    ProviderStatus.UNKNOWN:       "❓",
}

STATUS_COLOR: dict[ProviderStatus, str] = {
    ProviderStatus.WORKING:       "green",
    ProviderStatus.RATE_LIMITED:  "yellow",
    ProviderStatus.AUTH_REQUIRED: "blue",
    ProviderStatus.DOWN:          "red",
    ProviderStatus.UNKNOWN:       "dim",
}


@dataclass(slots=True)
class ModelInfo:
    alias: str
    display: str


@dataclass
class ProviderInfo:
    name: str
    model_list: list[ModelInfo]
    status: ProviderStatus = ProviderStatus.WORKING
    detail: str = ""
    latency_ms: Optional[int] = None

    @property
    def models(self) -> list[str]:
        return [m.alias for m in self.model_list]

    @property
    def status_label(self) -> str:
        emoji = STATUS_EMOJI.get(self.status, "?")
        return f"{emoji} {self.status.value}"

    @property
    def status_color(self) -> str:
        return STATUS_COLOR.get(self.status, "white")
    
    
def list_providers() -> list[ProviderInfo]:
    result: list[ProviderInfo] = []
    seen: set[str] = set()

    for name in PROVIDER_ORDER:
        if name in WORKING_PROVIDERS:
            entries = WORKING_PROVIDERS[name]
            model_list = [ModelInfo(alias=a, display=d) for a, d in entries]
            result.append(ProviderInfo(name=name, model_list=model_list))
            seen.add(name)

    for name, entries in WORKING_PROVIDERS.items():
        if name not in seen:
            model_list = [ModelInfo(alias=a, display=d) for a, d in entries]
            result.append(ProviderInfo(name=name, model_list=model_list))

    return result


def get_provider_info(name: str) -> Optional[ProviderInfo]:
    for p in list_providers():
        if p.name == name:
            return p
    return None


def get_provider_class(name: str) -> Optional[object]:
    try:
        from g4f import Provider
        cls = getattr(Provider, name, None)
        return cls
    except ImportError:
        return None


async def probe_provider(info: ProviderInfo) -> ProviderInfo:
    from g4f.client import AsyncClient

    provider_cls = get_provider_class(info.name)
    if provider_cls is None:
        info.status = ProviderStatus.DOWN
        info.detail = "class not found"
        return info

    model_alias = info.model_list[0].alias if info.model_list else "gpt-4o"
    start = time.monotonic()

    try:
        client = AsyncClient(provider=provider_cls)
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model_alias,
                messages=[{"role": "user", "content": PROBE_PROMPT}],
            ),
            timeout=PROBE_TIMEOUT,
        )
        content = response.choices[0].message.content if response.choices else ""
        if content:
            info.status = ProviderStatus.WORKING
            info.detail = "ok"
        else:
            info.status = ProviderStatus.DOWN
            info.detail = "empty response"

    except asyncio.TimeoutError:
        info.status = ProviderStatus.DOWN
        info.detail = f"timeout >{PROBE_TIMEOUT:.0f}s"

    except Exception as exc:
        msg = str(exc).lower()
        if "rate" in msg or "limit" in msg or "429" in msg:
            info.status = ProviderStatus.RATE_LIMITED
        elif "auth" in msg or "key" in msg or "401" in msg or "403" in msg:
            info.status = ProviderStatus.AUTH_REQUIRED
        else:
            info.status = ProviderStatus.DOWN
        info.detail = str(exc)[:120]

    finally:
        info.latency_ms = int((time.monotonic() - start) * 1000)

    return info