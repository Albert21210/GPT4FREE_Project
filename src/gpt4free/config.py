from __future__ import annotations
import json
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Self
from platformdirs import user_config_dir
from gpt4free.providers import DEFAULT_MODEL, DEFAULT_PROVIDER

APP_NAME: str = "gpt4free-tui"
CONFIG_VERSION: str = "2.0.0"

CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "version": {"type": "string"},
        "provider": {"type": "string"},
        "model": {"type": "string"},
        "stream": {"type": "boolean"},
        "syntax_theme": {"type": "string", "enum": ["monokai", "dracula", "solarized-dark", "github-dark"]},
        "max_history_items": {"type": "integer", "minimum": 10, "maximum": 1000},
        "prompt_history": {"type": "array", "items": {"type": "string"}},
        "last_session": {"type": "object", "properties": {
            "timestamp": {"type": "string"},
            "provider": {"type": "string"},
            "model": {"type": "string"}
        }},
        "stats": {"type": "object", "properties": {
            "total_queries": {"type": "integer"},
            "first_used": {"type": ["string", "null"]},
            "last_used": {"type": ["string", "null"]}
        }},
        "ui": {"type": "object", "properties": {
            "compact_mode": {"type": "boolean"},
            "show_timestamps": {"type": "boolean"},
            "color_scheme": {"type": "string"}
        }},
        "profiles": {"type": "object"},
        "active_profile": {"type": ["string", "null"]}
    },
    "required": ["version", "provider", "model"]
}

@dataclass
class AppConfig:

    # Core
    version: str = CONFIG_VERSION
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL

    # Behavior
    stream: bool = True
    syntax_theme: str = "monokai"
    max_history_items: int = 200

    # History
    prompt_history: list[str] = field(default_factory=list)

    # Session tracking
    last_session: dict[str, Any] = field(default_factory=dict)
    stats: dict[str, Any] = field(default_factory=lambda: {
        "total_queries": 0,
        "first_used": None,
        "last_used": None
    })

    # UI preferences
    ui: dict[str, Any] = field(default_factory=lambda: {
        "compact_mode": False,
        "show_timestamps": True,
        "color_scheme": "dark"
    })

    # Multiple profiles
    profiles: dict[str, dict] = field(default_factory=dict)
    active_profile: Optional[str] = None

    def add_to_history(self, prompt: str) -> None:
        if not prompt:
            return

        if prompt in self.prompt_history:
            self.prompt_history.remove(prompt)

        self.prompt_history.append(prompt)

        if len(self.prompt_history) > self.max_history_items:
            self.prompt_history = self.prompt_history[-self.max_history_items:]

        self.stats["total_queries"] = self.stats.get("total_queries", 0) + 1
        self.stats["last_used"] = datetime.now().isoformat()
        if not self.stats.get("first_used"):
            self.stats["first_used"] = datetime.now().isoformat()