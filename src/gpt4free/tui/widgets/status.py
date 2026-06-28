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


_CSS = """
StatusScreen {
    align: center middle;
    background: #00000099;
}
.ov-box {
    width: 94%;
    height: 88%;
    border: round #6c63ff;
    background: #0d0f17;
    padding: 1 2;
}
.ov-title {
    color: #6c63ff;
    text-style: bold;
    border-bottom: solid #1a1d2e;
    padding-bottom: 1;
    margin-bottom: 1;
}
DataTable {
    background: #0a0c14;
    border: solid #1a1d2e;
    height: 1fr;
}
DataTable > .datatable--header { background: #12152a; color: #6c63ff; text-style: bold; }
DataTable > .datatable--cursor { background: #1a1d40; }
"""


class StatusScreen(ModalScreen[None]):
    """Shows provider status table; press R to probe all live."""

    DEFAULT_CSS = _CSS
    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("r",      "probe",   "Re-check all"),
    ]
