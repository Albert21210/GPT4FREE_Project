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

    def user(self, text: str) -> None:
        """Add a user message."""
        w = Static(
            f"[bold #6c63ff]You ›[/bold #6c63ff]\n{text}",
            classes="msg-user",
        )
        self.mount(w)
        self._scroll_end()

    def bot_placeholder(self) -> Static:
        """Add an empty bot message that will be updated while streaming."""
        w = Static(
            "[bold #00cc66]GPT4FREE[/bold #00cc66]\n[dim]…[/dim]",
            classes="msg-bot",
        )
        self.mount(w)
        self._scroll_end()
        return w

    def update_bot(self, widget: Static, text: str) -> None:
        """Replace the content of a bot placeholder with streamed text."""
        widget.update(
            f"[bold #00cc66]GPT4FREE[/bold #00cc66]\n{self._escape(text)}"
        )
        self._scroll_end()

    def sys(self, text: str) -> Static:
        """Add a system/info message."""
        w = Static(text, classes="msg-sys")
        self.mount(w)
        self._scroll_end()
        return w

    def error(self, text: str) -> Static:
        """Add an error message."""
        w = Static(
            f"[bold red]✗ Error:[/bold red] {text}",
            classes="msg-error",
        )
        self.mount(w)
        self._scroll_end()
        return w

    def add_widget(self, widget: Static) -> None:
        """Mount an arbitrary Static widget."""
        self.mount(widget)
        self._scroll_end()

    def _scroll_end(self) -> None:
        try:
            scroller = self.parent
            if scroller is not None:
                scroller.scroll_end(animate=False)  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001
            pass

    @staticmethod
    def _escape(text: str) -> str:
        """Escape Rich markup characters in raw model output."""
        return text.replace("[", r"\[")
