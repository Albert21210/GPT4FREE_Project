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
        "active_profile": {"type": ["string", "null"]},
        "api_keys": {"type": "object"},
        "custom_providers": {"type": "object"},
        "proxy": {"type": ["string", "null"]},
        "force_proxy": {"type": "boolean"},
        "builtin_tools_enabled": {"type": "boolean"},
        "mcp_servers": {"type": "object"}
    },
    "required": ["version", "provider", "model"]
}
