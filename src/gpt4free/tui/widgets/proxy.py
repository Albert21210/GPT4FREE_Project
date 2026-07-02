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
