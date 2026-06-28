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


HELP_TEXT = """\
[bold #6c63ff]GPT4FREE Commands[/bold #6c63ff]

  [bold]/help[/bold]      — show this help
  [bold]/provider[/bold]  — change provider
  [bold]/model[/bold]     — change model
  [bold]/status[/bold]    — probe & show provider status table
  [bold]/clear[/bold]     — clear conversation history
  [bold]/new[/bold]       — start a fresh session
  [bold]/exit[/bold]      — quit

[dim]Tip: use ↑ ↓ arrows to navigate prompt history[/dim]
"""

BANNER = """\
  ██████╗ ██████╗ ████████╗██╗  ██╗███████╗██████╗ ███████╗███████╗
 ██╔════╝ ██╔══██╗╚══██╔══╝██║  ██║██╔════╝██╔══██╗██╔════╝██╔════╝
 ██║  ███╗██████╔╝   ██║   ███████║█████╗  ██████╔╝█████╗  █████╗
 ██║   ██║██╔═══╝    ██║   ╚════██║██╔══╝  ██╔══██╗██╔══╝  ██╔══╝
 ╚██████╔╝██║        ██║        ██║██║     ██║  ██║███████╗███████╗
  ╚═════╝ ╚═╝        ╚═╝        ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝"""
