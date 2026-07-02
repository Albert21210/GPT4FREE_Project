"""Modal screens for managing manual API keys and user-added custom providers.

Mirrors the shape of proxy.py: pure Textual modal + AppConfig read/write done
by the caller (app.py) after dismiss(), same as ProxyScreen. Two screens:

  KeysScreen           — attach an API key to a *built-in* provider
                          (Cerebras, Gemini, HuggingFace, ...) that otherwise
                          shows up as auth_required in `status`.
  CustomProviderScreen — register your own OpenAI-compatible endpoint
                          (base_url + api_key + model list) that isn't part
                          of the built-in g4f registry at all.
"""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, Static

from gpt4free.providers import ProviderInfo


_CSS = """
KeysScreen, CustomProviderScreen {
    align: center middle;
    background: #00000099;
}
.keys-box, .cust-box {
    width: 76;
    height: auto;
    max-height: 90%;
    border: round #6c63ff;
    background: #0d0f17;
    padding: 1 2;
}
.keys-title, .cust-title {
    color: #6c63ff;
    text-style: bold;
    border-bottom: solid #1a1d2e;
    padding-bottom: 1;
    margin-bottom: 1;
}
.keys-hint, .cust-hint {
    color: #6f7390;
    margin-bottom: 1;
}
.keys-input, .cust-input {
    background: #12152a;
    border: solid #252850;
    color: #e0e0ff;
    margin-bottom: 1;
}
.keys-input:focus, .cust-input:focus { border: solid #6c63ff; }

.keys-list {
    background: #0a0c14;
    border: solid #1a1d2e;
    height: 10;
    margin-bottom: 1;
}
.keys-list > ListItem { color: #b0b0d0; padding: 0 1; }
.keys-list > ListItem.--highlight { background: #1a1d40; color: #ffffff; }

.keys-buttons, .cust-buttons { height: auto; align: right middle; }
.keys-buttons Button, .cust-buttons Button { margin-left: 1; }
.field-label { color: #9f99ff; margin-top: 1; }
"""


class KeysScreen(ModalScreen[Optional[tuple[str, str]]]):
    """
    Attach an API key to one of the built-in providers.

    Dismisses with:
      - None              → cancelled
      - (provider, "")     → key removed for that provider
      - (provider, key)    → key saved for that provider
    """

    DEFAULT_CSS = _CSS
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, providers: list[ProviderInfo], current_keys: dict[str, str]) -> None:
        super().__init__()
        self._providers = providers
        self._current_keys = current_keys
        self._selected: Optional[str] = None

    def _item_label(self, p: ProviderInfo) -> str:
        has_key = "🔑 set" if self._current_keys.get(p.name) else "[dim]no key[/dim]"
        auth_tag = "[dim](needs auth)[/dim]" if p.needs_auth else "[dim](no auth needed)[/dim]"
        return f"[bold]{p.name}[/bold]  {auth_tag}  — {has_key}"

    def compose(self) -> ComposeResult:
        with Vertical(classes="keys-box"):
            yield Label("  🔑  API Keys for Built-in Providers", classes="keys-title")
            yield Static(
                "Pick a provider below, then paste its key and press Save.\n"
                "Unlocks providers that show up as auth_required in status.",
                classes="keys-hint",
            )
            yield ListView(
                *[
                    ListItem(Label(self._item_label(p)), name=p.name)
                    for p in self._providers
                ],
                classes="keys-list",
                id="lst",
            )
            yield Label("Key for: [dim]— select a provider above —[/dim]", classes="field-label", id="selected-label")
            yield Input(
                placeholder="paste API key here (leave empty + Save to remove)",
                classes="keys-input",
                id="key-input",
                password=True,
            )
            with Horizontal(classes="keys-buttons"):
                yield Button("Cancel", id="cancel-btn", variant="default")
                yield Button("Save", id="save-btn", variant="primary")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._selected = event.item.name
        label = self.query_one("#selected-label", Label)
        label.update(f"Key for: [bold]{self._selected}[/bold]")
        inp = self.query_one("#key-input", Input)
        inp.value = self._current_keys.get(self._selected, "")
        inp.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_save(self) -> None:
        if not self._selected:
            self.query_one("#selected-label", Label).update(
                "[bold red]Pick a provider from the list first[/bold red]"
            )
            return
        key = self.query_one("#key-input", Input).value.strip()
        self.dismiss((self._selected, key))


class CustomProviderScreen(ModalScreen[Optional[dict]]):
    """
    Register a user-added OpenAI-compatible provider (e.g. Together AI, a
    self-hosted endpoint, or any other service with a `/chat/completions`
    route) that isn't part of the built-in g4f registry.

    Dismisses with:
      - None    → cancelled
      - dict     → {"name": ..., "base_url": ..., "api_key": ..., "models": [...]}
    """

    DEFAULT_CSS = _CSS
    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(classes="cust-box"):
            yield Label("  ➕  Add Custom Provider", classes="cust-title")
            yield Static(
                "For your own OpenAI-compatible API (e.g. Together, a\n"
                "self-hosted server, or any other provider with your own token).",
                classes="cust-hint",
            )
            yield Label("Name", classes="field-label")
            yield Input(placeholder="e.g. Together", classes="cust-input", id="name-input")
            yield Label("Base URL", classes="field-label")
            yield Input(
                placeholder="e.g. https://api.together.xyz/v1",
                classes="cust-input",
                id="url-input",
            )
            yield Label("API key (optional)", classes="field-label")
            yield Input(placeholder="sk-...", classes="cust-input", id="key-input", password=True)
            yield Label("Models (comma-separated)", classes="field-label")
            yield Input(
                placeholder="e.g. meta-llama/Llama-3-70b-chat-hf, Qwen/Qwen2.5-72B-Instruct",
                classes="cust-input",
                id="models-input",
            )
            yield Static("", id="error-label", classes="cust-hint")
            with Horizontal(classes="cust-buttons"):
                yield Button("Cancel", id="cancel-btn", variant="default")
                yield Button("Add", id="save-btn", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#name-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self.action_save()
        elif event.button.id == "cancel-btn":
            self.action_cancel()
