from __future__ import annotations
import json
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional, Self

from gpt4free.config.config_schema import CONFIG_SCHEMA, CONFIG_VERSION
from gpt4free.providers import DEFAULT_MODEL, DEFAULT_PROVIDER


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

    api_keys: dict[str, str] = field(default_factory=dict)
    custom_providers: dict[str, dict] = field(default_factory=dict)
    proxy: Optional[str] = None
    force_proxy: bool = False

    # Tools / MCP
    builtin_tools_enabled: bool = True
    mcp_servers: dict[str, dict] = field(default_factory=dict)

    def set_proxy(self, proxy_url: str, force: bool = False) -> None:
        self.proxy = proxy_url.strip() or None
        self.force_proxy = force

    def clear_proxy(self) -> None:
        self.proxy = None
        self.force_proxy = False

    def set_api_key(self, provider: str, key: str) -> None:
        if key:
            self.api_keys[provider] = key
        else:
            self.api_keys.pop(provider, None)

    def get_api_key(self, provider: str) -> Optional[str]:
        return self.api_keys.get(provider)

    def add_custom_provider(
        self,
        name: str,
        base_url: str,
        models: list[dict[str, str]],
        api_key: str = "",
    ) -> None:
        self.custom_providers[name] = {
            "base_url": base_url,
            "api_key": api_key,
            "models": models,
        }

    def remove_custom_provider(self, name: str) -> None:
        self.custom_providers.pop(name, None)

    def add_mcp_server(
        self,
        name: str,
        command: str,
        args: Optional[list[str]] = None,
        env: Optional[dict[str, str]] = None,
        enabled: bool = True,
    ) -> None:
        """Register a local MCP server (launched as `command args...` over stdio)."""
        self.mcp_servers[name] = {
            "command": command,
            "args": args or [],
            "env": env or {},
            "enabled": enabled,
        }

    def remove_mcp_server(self, name: str) -> None:
        self.mcp_servers.pop(name, None)

    def set_mcp_server_enabled(self, name: str, enabled: bool) -> None:
        if name in self.mcp_servers:
            self.mcp_servers[name]["enabled"] = enabled

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

    def get_recent_history(self, n: int = 10) -> list[str]:
        return self.prompt_history[-n:]

    def search_history(self, query: str) -> list[str]:
        return [p for p in reversed(self.prompt_history) if query.lower() in p.lower()]

    def clear_history(self) -> None:
        self.prompt_history.clear()

    def save_profile(self, name: str) -> None:
        self.profiles[name] = {
            "provider": self.provider,
            "model": self.model,
            "stream": self.stream,
            "syntax_theme": self.syntax_theme,
            "ui": self.ui.copy()
        }

    def load_profile(self, name: str) -> None:
        if name not in self.profiles:
            raise ValueError(f"Profile '{name}' not found")

        profile = self.profiles[name]
        self.provider = profile.get("provider", self.provider)
        self.model = profile.get("model", self.model)
        self.stream = profile.get("stream", self.stream)
        self.syntax_theme = profile.get("syntax_theme", self.syntax_theme)
        self.ui.update(profile.get("ui", {}))
        self.active_profile = name

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["version"] = CONFIG_VERSION
        data["_meta"] = {
            "saved_at": datetime.now().isoformat(),
            "python_version": __import__("sys").version,
            "config_hash": self._get_hash()
        }
        return data

    def _get_hash(self) -> str:
        data = asdict(self)
        data.pop("_meta", None)
        return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:8]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if "version" not in data:
            data = cls._migrate_v1_to_v2(data)

        cls._validate(data)

        known = set(cls.__dataclass_fields__)
        filtered = {k: v for k, v in data.items() if k in known}

        return cls(**filtered)

    @staticmethod
    def _validate(data: dict[str, Any]) -> None:
        try:
            import jsonschema
            jsonschema.validate(data, CONFIG_SCHEMA)
        except ImportError:
            if "provider" not in data or "model" not in data:
                raise ValueError("Missing required fields: provider, model")
        except jsonschema.ValidationError as e:
            raise ValueError(f"Invalid config: {e.message}")

    @staticmethod
    def _migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
        data["version"] = "2.0.0"
        data.setdefault("stats", {
            "total_queries": 0,
            "first_used": None,
            "last_used": None
        })
        data.setdefault("ui", {
            "compact_mode": False,
            "show_timestamps": True,
            "color_scheme": "dark"
        })
        data.setdefault("profiles", {})
        data.setdefault("api_keys", {})
        data.setdefault("custom_providers", {})
        data.setdefault("proxy", None)
        data.setdefault("force_proxy", False)
        data.setdefault("builtin_tools_enabled", True)
        data.setdefault("mcp_servers", {})
        return data
