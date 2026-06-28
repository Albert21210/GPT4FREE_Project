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

    def compose(self) -> ComposeResult:
        with Vertical(classes="ov-box"):
            yield Label(
                "  📊  Provider Status  ·  [bold]Esc[/bold] close  "
                "·  [bold]R[/bold] live probe all",
                classes="ov-title",
            )
            tbl: DataTable[str] = DataTable(id="tbl")
            tbl.add_columns("Provider", "Status", "Latency", "Models")
            yield tbl

    def on_mount(self) -> None:
        self._fill(list_providers())

    def _fill(self, infos: list[ProviderInfo]) -> None:
        tbl = self.query_one("#tbl", DataTable)
        tbl.clear()
        for p in infos:
            color = STATUS_COLOR.get(p.status, "white")
            emoji = STATUS_EMOJI.get(p.status, "?")
            lat = f"{p.latency_ms}ms" if p.latency_ms is not None else "—"
            preview = ", ".join(m.display for m in p.model_list[:4])
            if len(p.model_list) > 4:
                preview += f" +{len(p.model_list) - 4}"
            tbl.add_row(
                p.name,
                f"[{color}]{emoji} {p.status.value}[/{color}]",
                lat,
                preview,
            )
