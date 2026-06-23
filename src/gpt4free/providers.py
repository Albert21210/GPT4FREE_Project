from __future__ import annotations

from enum import Enum

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