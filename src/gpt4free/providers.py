from __future__ import annotations

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