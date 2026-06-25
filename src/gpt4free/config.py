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
        return data
    

class ConfigManager:

    def __init__(self, app_name: str = APP_NAME):
        self.app_name = app_name
        self._config_path = self._get_config_path()
        self._backup_path = self._config_path.parent / "config.backups"
        self._backup_path.mkdir(parents=True, exist_ok=True)

    def _get_config_path(self) -> Path:
        path = Path(user_config_dir(self.app_name))
        path.mkdir(parents=True, exist_ok=True)
        return path / "config.json"
    
    def load(self) -> AppConfig:
        if not self._config_path.exists():
            return AppConfig()

        self._backup_current()

        try:
            raw = self._config_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return AppConfig.from_dict(data)
        except (json.JSONDecodeError, ValueError, TypeError):
            return self._recover_from_backup()
        
    def save(self, config: AppConfig) -> None:
        self._backup_current()

        temp_path = self._config_path.with_suffix(".tmp")
        try:
            temp_path.write_text(
                json.dumps(config.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            temp_path.replace(self._config_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    def _backup_current(self) -> None:
        if not self._config_path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self._backup_path / f"config_{timestamp}.json"
        self._config_path.copy(backup_file)

        # Keep only last 10 backups
        backups = sorted(self._backup_path.glob("config_*.json"))
        for old_backup in backups[:-10]:
            old_backup.unlink()

    def _recover_from_backup(self) -> AppConfig:
        backups = sorted(self._backup_path.glob("config_*.json"))
        if not backups:
            return AppConfig()

        latest = backups[-1]
        try:
            raw = latest.read_text(encoding="utf-8")
            data = json.loads(raw)
            return AppConfig.from_dict(data)
        except Exception:
            return AppConfig()
        
    def list_backups(self) -> list[Path]:
        return sorted(self._backup_path.glob("config_*.json"))
    
    def rollback(self, backup_name: str) -> None:
        backup_path = self._backup_path / backup_name
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup '{backup_name}' not found")

        backup_path.copy(self._config_path)