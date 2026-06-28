"""Scrollable chat log widget with Rich markup rendering."""

from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static


class ChatLog(Widget):
    """Vertical log of chat messages, each rendered as a Static widget."""

    DEFAULT_CSS = """
    ChatLog {
        height: auto;
        padding: 0;
    }
    """
