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