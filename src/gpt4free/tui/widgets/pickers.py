"""Modal picker screens for provider and model selection."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListItem, ListView

from gpt4free.providers import ModelInfo, ProviderInfo, STATUS_EMOJI


_MODAL_CSS = """
.modal-bg {
    align: center middle;
    background: #00000099;
}
.modal-box {
    width: 70%;
    height: 78%;
    border: round #6c63ff;
    background: #0d0f17;
    padding: 1 2;
}
.modal-title {
    color: #6c63ff;
    text-style: bold;
    border-bottom: solid #1a1d2e;
    padding-bottom: 1;
    margin-bottom: 1;
}
.modal-filter {
    background: #12152a;
    border: solid #252850;
    color: #e0e0ff;
    margin-bottom: 1;
}
.modal-filter:focus { border: solid #6c63ff; }

ListView {
    background: #0a0c14;
    border: solid #1a1d2e;
    height: 1fr;
}
ListView > ListItem { color: #b0b0d0; padding: 0 1; }
ListView > ListItem.--highlight { background: #1a1d40; color: #ffffff; }
ListView > ListItem:hover { background: #141730; }
"""


class ProviderPickerScreen(ModalScreen[Optional[str]]):
    """Fuzzy-searchable provider selection modal."""

    DEFAULT_CSS = _MODAL_CSS
    BINDINGS = [("escape", "dismiss_none", "Cancel")]

    def __init__(self, providers: list[ProviderInfo]) -> None:
        super().__init__()
        self._providers = providers

    def _item_label(self, p: ProviderInfo) -> str:
        emoji = STATUS_EMOJI.get(p.status, "?")
        models_preview = ", ".join(m.display for m in p.model_list[:3])
        if len(p.model_list) > 3:
            models_preview += f" +{len(p.model_list) - 3}"
        return f"{emoji} [bold]{p.name}[/bold]  [dim][{models_preview}][/dim]"

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-box"):
            yield Label("  🔌  Select Provider", classes="modal-title")
            yield Input(placeholder="🔍 type to filter…", classes="modal-filter", id="flt")
            yield ListView(
                *[
                    ListItem(Label(self._item_label(p)), name=p.name)
                    for p in self._providers
                ],
                id="lst",
            )

    def action_dismiss_none(self) -> None:
        self.dismiss(None)

    def on_input_changed(self, event: Input.Changed) -> None:
        q = event.value.lower()
        lv = self.query_one("#lst", ListView)
        lv.clear()
        for p in self._providers:
            if q in p.name.lower() or any(q in m.display.lower() for m in p.model_list):
                lv.append(ListItem(Label(self._item_label(p)), name=p.name))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss(event.item.name)


class ModelPickerScreen(ModalScreen[Optional[str]]):
    """Fuzzy-searchable model selection modal."""

    DEFAULT_CSS = _MODAL_CSS
    BINDINGS = [("escape", "dismiss_none", "Cancel")]

    def __init__(self, model_list: list[ModelInfo]) -> None:
        super().__init__()
        self._models = model_list

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-box"):
            yield Label("  🧠  Select Model", classes="modal-title")
            yield Input(placeholder="🔍 type to filter…", classes="modal-filter", id="flt")
            yield ListView(
                *[
                    ListItem(
                        Label(f"◆ [bold]{m.display}[/bold]  [dim]{m.alias}[/dim]"),
                        name=m.alias,
                    )
                    for m in self._models
                ],
                id="lst",
            )

    def action_dismiss_none(self) -> None:
        self.dismiss(None)

    def on_input_changed(self, event: Input.Changed) -> None:
        q = event.value.lower()
        lv = self.query_one("#lst", ListView)
        lv.clear()
        for m in self._models:
            if q in m.display.lower() or q in m.alias.lower():
                lv.append(
                    ListItem(
                        Label(f"◆ [bold]{m.display}[/bold]  [dim]{m.alias}[/dim]"),
                        name=m.alias,
                    )
                )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss(event.item.name)
