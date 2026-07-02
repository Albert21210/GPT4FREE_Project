"""Live provider status screen with optional probing."""
from __future__ import annotations
import os
from typing import Optional
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import DataTable, Label
from gpt4free.config import AppConfig
from gpt4free.providers import (
    ProviderInfo,
    ProviderStatus,
    STATUS_COLOR,
    STATUS_EMOJI,
    list_providers,
    probe_all,
)

PROXY_ENV_VAR = "G4F_PROXY"

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

    def __init__(self, cfg: Optional[AppConfig] = None) -> None:
        super().__init__()
        self._cfg = cfg

    def compose(self) -> ComposeResult:
        with Vertical(classes="ov-box"):
            yield Label(
                "  📊  Provider Status  ·  [bold]Esc[/bold] close  "
                "·  [bold]R[/bold] live probe all",
                classes="ov-title",
            )
            tbl: DataTable[str] = DataTable(id="tbl")
            tbl.add_columns("Provider", "Status", "Latency", "Detail", "Models")
            yield tbl

    def on_mount(self) -> None:
        custom = self._cfg.custom_providers if self._cfg else None
        self._fill(list_providers(custom))

    def _fill(self, infos: list[ProviderInfo]) -> None:
        tbl = self.query_one("#tbl", DataTable)
        tbl.clear()
        for p in infos:
            color = STATUS_COLOR.get(p.status, "white")
            emoji = STATUS_EMOJI.get(p.status, "?")
            lat = f"{p.latency_ms}ms" if p.latency_ms is not None else "—"
            detail = p.detail or "—"
            if len(detail) > 40:
                detail = detail[:37] + "..."
            name = p.name + (" 🛠" if p.is_custom else "")
            preview = ", ".join(m.display for m in p.model_list[:4])
            if len(p.model_list) > 4:
                preview += f" +{len(p.model_list) - 4}"
            tbl.add_row(
                name,
                f"[{color}]{emoji} {p.status.value}[/{color}]",
                lat,
                f"[dim]{detail}[/dim]",
                preview,
            )

    async def action_probe(self) -> None:
        tbl = self.query_one("#tbl", DataTable)
        tbl.clear()
        tbl.add_row("Probing all providers…", "", "", "", "")

        custom = self._cfg.custom_providers if self._cfg else None
        api_keys = self._cfg.api_keys if self._cfg else None
        proxy = os.environ.get(PROXY_ENV_VAR) or None

        infos = await probe_all(list_providers(custom), proxy=proxy, api_keys=api_keys)
        self._fill(infos)
