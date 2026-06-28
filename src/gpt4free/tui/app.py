"""
GPT4FREE TUI — Gemini CLI style terminal interface.

Keybindings:
  /help         — show commands
  /provider     — pick provider
  /model        — pick model
  /status       — probe & show provider status
  /clear        — clear conversation
  /new          — new session
  Ctrl+C / /exit — quit
"""

from __future__ import annotations

import asyncio
from typing import Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Footer, Input, Label, Static

from gpt4free.chat import ChatSession
from gpt4free.config import AppConfig, load_config, save_config
from gpt4free.providers import (
    ProviderInfo,
    list_providers,
    probe_all,
)
from gpt4free.tui.widgets import (
    ChatLog,
    ModelPickerScreen,
    ProviderPickerScreen,
    StatusScreen,
)
