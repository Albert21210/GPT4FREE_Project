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

    /* ── Chat log area ───────────────────────────────────────── */
    #chat-scroll {
        height: 1fr;
        margin: 0 1;
        background: #0a0c14;
        border: solid #1a1d2e;
        border-title-color: #3d3f5c;
        scrollbar-color: #6c63ff #1a1d2e;
        scrollbar-size: 1 1;
    }
    ChatLog {
        padding: 1 2;
    }

    /* ── Message styles ──────────────────────────────────────── */
    .msg-user {
        color: #e0e0ff;
        border-left: solid #6c63ff;
        background: #12152a;
        padding: 0 1;
        margin-bottom: 1;
    }
    .msg-bot {
        color: #c8ffc8;
        border-left: solid #00cc66;
        background: #0a140a;
        padding: 0 1;
        margin-bottom: 1;
    }
    .msg-sys {
        color: #3d3f5c;
        text-style: italic;
        margin-bottom: 1;
    }
    .msg-error {
        color: #ff6666;
        border-left: solid #cc2222;
        background: #1a0a0a;
        padding: 0 1;
        margin-bottom: 1;
    }
    .msg-help {
        color: #9f99ff;
        border-left: solid #4a44cc;
        background: #0d0f20;
        padding: 0 1;
        margin-bottom: 1;
    }

    /* ── Input area ──────────────────────────────────────────── */
    #input-area {
        height: 5;
        background: #0d0f17;
        border-top: solid #1a1d2e;
        padding: 1 1 0 1;
    }
    #input-row {
        height: 3;
        align: left middle;
    }
    #caret {
        color: #6c63ff;
        width: 4;
        content-align: center middle;
        text-style: bold;
    }
    #prompt {
        width: 1fr;
        background: #12152a;
        border: solid #252850;
        color: #e0e0ff;
        padding: 0 1;
    }
    #prompt:focus {
        border: solid #6c63ff;
        background: #0f1228;
    }

    /* ── Status bar ──────────────────────────────────────────── */
    #status-bar {
        height: 1;
        background: #12152a;
        layout: horizontal;
        padding: 0 1;
    }
    #sb-left  { width: 1fr;  color: #6c63ff; }
    #sb-mid   { width: auto; color: #3d3f5c; content-align: center middle; }
    #sb-right { width: auto; color: #3d3f5c; }

    Footer {
        background: #0d0f17;
        color: #3d3f5c;
    }
    Footer > .footer--highlight { background: #6c63ff; color: white; }
    Footer > .footer--key       { color: #6c63ff; }
    """
