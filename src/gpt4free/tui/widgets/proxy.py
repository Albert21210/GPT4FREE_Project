"""Modal screen for configuring an optional outbound proxy.

A proxy is only needed for providers that are geoblocked at the company
level (Gemini, MetaAI, Grok — see gpt4free.providers.PROXY_REQUIRED_PROVIDERS).
By default it stays OFF and is only applied to those providers; users can
opt in to routing every provider through it via the "force" checkbox.
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Static

from gpt4free.providers import PROXY_REQUIRED_PROVIDERS

_CSS = """
ProxyScreen {
    align: center middle;
    background: #00000099;
}
.proxy-box {
    width: 70;
    height: auto;
    border: round #6c63ff;
    background: #0d0f17;
    padding: 1 2;
}
.proxy-title {
    color: #6c63ff;
    text-style: bold;
    border-bottom: solid #1a1d2e;
    padding-bottom: 1;
    margin-bottom: 1;
}
.proxy-hint {
    color: #6f7390;
    margin-bottom: 1;
}
.proxy-input {
    background: #12152a;
    border: solid #252850;
    color: #e0e0ff;
    margin-bottom: 1;
}
.proxy-input:focus { border: solid #6c63ff; }
.proxy-checkbox { margin-bottom: 1; color: #b0b0d0; }
.proxy-status { color: #6f7390; margin-bottom: 1; }
.proxy-buttons { height: auto; align: right middle; }
.proxy-buttons Button { margin-left: 1; }
"""


class ProxyScreen(ModalScreen[Optional[tuple[Optional[str], bool]]]):
    """
    Lets the user set/clear a proxy URL and whether it applies to every
    provider or only the geoblocked ones (Gemini/MetaAI/Grok).

    Dismisses with:
      - None                  → cancelled, no change
      - (None, False)         → proxy cleared
      - (proxy_url, force)    → proxy saved
    """

    DEFAULT_CSS = _CSS
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "save", "Save"),
    ]

    def __init__(self, current_proxy: Optional[str] = None, current_force: bool = False) -> None:
        super().__init__()
        self._current_proxy = current_proxy
        self._current_force = current_force

    def compose(self) -> ComposeResult:
        geoblocked = ", ".join(sorted(PROXY_REQUIRED_PROVIDERS))
        with Vertical(classes="proxy-box"):
            yield Label("  🌐  Proxy Settings", classes="proxy-title")
            yield Static(
                f"Used by default only for: [bold]{geoblocked}[/bold]\n"
                "Leave empty and press Save to remove an existing proxy.",
                classes="proxy-hint",
            )
            yield Input(
                value=self._current_proxy or "",
                placeholder="socks5://127.0.0.1:1080  or  http://user:pass@host:port",
                classes="proxy-input",
                id="proxy-input",
            )
            yield Checkbox(
                "Route ALL providers through this proxy (not just geoblocked ones)",
                value=self._current_force,
                classes="proxy-checkbox",
                id="force-checkbox",
            )
            yield Static(self._status_text(), id="status", classes="proxy-status")
            with Horizontal(classes="proxy-buttons"):
                yield Button("Cancel", id="cancel-btn", variant="default")
                yield Button("Save", id="save-btn", variant="primary")

    def _status_text(self) -> str:
        if self._current_proxy:
            scope = "ALL providers" if self._current_force else "geoblocked providers only"
            return f"Current: [bold]{self._current_proxy}[/bold]  ·  scope: {scope}"
        return "Current: [dim]not set[/dim]"

    def on_mount(self) -> None:
        self.query_one("#proxy-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)
