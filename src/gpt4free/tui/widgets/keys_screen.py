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
