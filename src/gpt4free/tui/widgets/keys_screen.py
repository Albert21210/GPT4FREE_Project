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
