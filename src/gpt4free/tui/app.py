"""
GPT4FREE TUI — Gemini CLI style terminal interface.

Keybindings:
  /help         — show commands
  /provider     — pick provider
  /model        — pick model
  /proxy        — configure outbound proxy
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
    CustomProviderScreen,
    KeysScreen,
    ModelPickerScreen,
    ProviderPickerScreen,
    ProxyScreen,
    StatusScreen,
)


HELP_TEXT = """\
[bold #6c63ff]GPT4FREE Commands[/bold #6c63ff]

  [bold]/help[/bold]      — show this help
  [bold]/provider[/bold]  — change provider
  [bold]/model[/bold]     — change model
  [bold]/proxy[/bold]     — configure outbound proxy
  [bold]/keys[/bold]      — attach an API key to a built-in provider
  [bold]/custom[/bold]    — add your own OpenAI-compatible provider
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


class GPT4FREETUI(App[None]):
    """Gemini CLI-style TUI for GPT4FREE."""

    CSS = """
    /* ── Global ──────────────────────────────────────────────── */
    Screen {
        background: #0d0f17;
        layers: base overlay;
    }

    /* ── Banner ──────────────────────────────────────────────── */
    #banner-wrap {
        height: auto;
        padding: 1 2 0 2;
        background: #0d0f17;
        border-bottom: solid #1a1d2e;
    }
    #banner {
        color: #6c63ff;
        text-style: bold;
        text-align: center;
    }
    #banner-sub {
        color: #3d3f5c;
        text-align: center;
        padding: 0 0 1 0;
    }
