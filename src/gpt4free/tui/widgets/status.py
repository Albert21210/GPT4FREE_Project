"""Live provider status screen with optional probing."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Label

from gpt4free.providers import (
    ProviderInfo,
    ProviderStatus,
    STATUS_COLOR,
    STATUS_EMOJI,
    list_providers,
    probe_all,
)
