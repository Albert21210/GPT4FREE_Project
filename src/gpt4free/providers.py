from __future__ import annotations

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