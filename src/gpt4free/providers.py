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
    # Qwen - без авторизации(не работает, нужна доработка)
    "Qwen": [
        ("qwen3.7-plus", "Qwen3.7 Plus"),
        ("qwen3.7-max", "Qwen3.7 Max"),
        ("qwen3.6-plus", "Qwen3.6 Plus"),
    ],
    # MetaAI - без авторизации(не всегда)
    "MetaAI": [
        ("meta-ai", "Meta AI (Llama)"),
    ],
    # Yqcloud - без авторизации
    "Yqcloud": [
        ("gpt-4", "GPT-4"),
    ],
    # Felo - без авторизации
    "Felo": [
        ("felo-chat", "Felo Chat"),
        ("felo-search", "Felo Search"),
    ],
    # Pi - без авторизации
    "Pi": [
        ("pi", "Inflection Pi"),
    ],
    # DeepInfra - без авторизации(перестал работать)
    "DeepInfra": [
        ("MiniMaxAI/MiniMax-M2.5", "MiniMax M2.5"),
    ],
    # GeminiPro - без авторизации (web-сессия)(не всегда)
    "GeminiPro": [
        ("models/gemini-2.5-flash", "Gemini 2.5 Flash"),
    ],
    # OpenRouterFree - без авторизации(не всегда)
    "OpenRouterFree": [
        ("openrouter/free", "OpenRouter Free Pool"),
    ],
    # Groq - без авторизации (часть моделей доступна анонимно)
    "Groq": [
        ("openai/gpt-oss-120b", "GPT-OSS 120B"),
    ],
    # Cerebras - требует ключ, но очень быстрый инференс
    "Cerebras": [
        ("llama-3.3-70b", "Llama 3.3 70B"),
        ("llama3.1-70b", "Llama 3.1 70B"),
    ],
    # Gemini - официальный веб-доступ, требует cookies/auth
    "Gemini": [
        ("gemini-3.1-pro", "Gemini 3.1 Pro"),
        ("gemini-3.5-flash", "Gemini 3.5 Flash"),
    ],
    # Grok - требует авторизацию
    "Grok": [
        ("grok-4", "Grok 4"),
        ("grok-3", "Grok 3"),
    ],
}

NO_AUTH_PROVIDERS: frozenset[str] = frozenset({
    "PollinationsAI", "Qwen", "MetaAI", "Yqcloud", "Felo", "Pi",
    "DeepInfra", "GeminiPro", "OpenRouterFree", "Groq", "Cerebras", "Gemini", "Grok"
})

PROXY_REQUIRED_PROVIDERS: frozenset[str] = frozenset

PROVIDER_ORDER: list[str] = [
    "PollinationsAI",
]

DEFAULT_PROVIDER: str = "PollinationsAI"
DEFAULT_MODEL: str = "openai"

PROBE_PROMPT: str = "Reply with one word: hello"
PROBE_TIMEOUT: float = 12.0
PROBE_TIMEOUT_BROWSER: float = 60.0


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
    needs_auth: bool = False
    needs_proxy: bool = False
    is_custom: bool = False
    base_url: Optional[str] = None
    requires_browser: bool = False

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


def custom_providers_to_info(
    custom_providers: Optional[dict[str, dict]] = None,
) -> list[ProviderInfo]:
    """Turn config.py's `custom_providers` dict into ProviderInfo entries."""
    if not custom_providers:
        return []

    result: list[ProviderInfo] = []
    for name, cfg in custom_providers.items():
        models = cfg.get("models", [])
        model_list = [
            ModelInfo(alias=m["alias"], display=m.get("display", m["alias"]))
            for m in models
        ]
        result.append(ProviderInfo(
            name=name,
            model_list=model_list,
            needs_auth=bool(cfg.get("api_key")),
            needs_proxy=False,
            is_custom=True,
            base_url=cfg.get("base_url"),
        ))
    return result


def list_providers(custom_providers: Optional[dict[str, dict]] = None) -> list[ProviderInfo]:
    result: list[ProviderInfo] = []
    seen: set[str] = set()

    for name in PROVIDER_ORDER:
        if name in WORKING_PROVIDERS:
            entries = WORKING_PROVIDERS[name]
            model_list = [ModelInfo(alias=a, display=d) for a, d in entries]
            result.append(ProviderInfo(
                name=name,
                model_list=model_list,
                needs_auth=name not in NO_AUTH_PROVIDERS,
                needs_proxy=name in PROXY_REQUIRED_PROVIDERS,
            ))
            seen.add(name)

    for name, entries in WORKING_PROVIDERS.items():
        if name not in seen:
            model_list = [ModelInfo(alias=a, display=d) for a, d in entries]
            result.append(ProviderInfo(
                name=name,
                model_list=model_list,
                needs_auth=name not in NO_AUTH_PROVIDERS,
                needs_proxy=name in PROXY_REQUIRED_PROVIDERS,
            ))

    result.extend(custom_providers_to_info(custom_providers))

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


async def probe_all(
    providers: list[ProviderInfo],
    concurrency: int = 4,
) -> list[ProviderInfo]:
    sem = asyncio.Semaphore(concurrency)

    async def _bounded(p: ProviderInfo) -> ProviderInfo:
        async with sem:
            return await probe_provider(p)

    return list(await asyncio.gather(*(_bounded(p) for p in providers)))