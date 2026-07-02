"""
GPT4FREE TUI — Gemini CLI style terminal interface.

Keybindings:
  /help         — show commands
  /provider     — pick provider
  /model        — pick model
  /status       — probe & show provider status
  /clear        — clear conversation
  /new          — new session
  Ctrl+C / /exit — quit
"""

from __future__ import annotations

import asyncio
from typing import Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Button, Footer, Input, Label, Static

from gpt4free.chat import ChatSession
from gpt4free.config import AppConfig, load_config, save_config
from gpt4free.providers import (
    ProviderInfo,
    list_providers,
    probe_all,
)
from gpt4free.tui.widgets import (
    ChatLog,
    ModelPickerScreen,
    ProviderPickerScreen,
    StatusScreen,
)


HELP_TEXT = """\
[bold #6c63ff]GPT4FREE Commands[/bold #6c63ff]

  [bold]/help[/bold]      — show this help
  [bold]/provider[/bold]  — change provider
  [bold]/model[/bold]     — change model
  [bold]/status[/bold]    — probe & show provider status table
  [bold]/clear[/bold]     — clear conversation history
  [bold]/new[/bold]       — start a fresh session
  [bold]/exit[/bold]      — quit

[dim]Tip: use ↑ ↓ arrows to navigate prompt history[/dim]
"""

BANNER = """\
  ██████╗ ██████╗ ████████╗██╗  ██╗███████╗██████╗ ███████╗███████╗
 ██╔════╝ ██╔══██╗╚══██╔══╝██║  ██║██╔════╝██╔══██╗██╔════╝██╔════╝
 ██║  ███╗██████╔╝   ██║   ███████║█████╗  ██████╔╝█████╗  █████╗
 ██║   ██║██╔═══╝    ██║   ╚════██║██╔══╝  ██╔══██╗██╔══╝  ██╔══╝
 ╚██████╔╝██║        ██║        ██║██║     ██║  ██║███████╗███████╗
  ╚═════╝ ╚═╝        ╚═╝        ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝"""


class GPT4FREETUI(App[None]):
    """Gemini CLI-style TUI for GPT4FREE."""

    CSS = """
    /* ── Global ──────────────────────────────────────────────── */
    Screen {
        background: #0d0f17;
        layers: base overlay;
    }

    /* ── Banner ──────────────────────────────────────────────── */
    #banner-wrap {
        height: auto;
        padding: 1 2 0 2;
        background: #0d0f17;
        border-bottom: solid #1a1d2e;
    }
    #banner {
        color: #6c63ff;
        text-style: bold;
        text-align: center;
    }
    #banner-sub {
        color: #3d3f5c;
        text-align: center;
        padding: 0 0 1 0;
    }

    /* ── Chat log area ───────────────────────────────────────── */
    #chat-scroll {
        height: 1fr;
        margin: 0 1;
        background: #0a0c14;
        border: solid #1a1d2e;
        border-title-color: #3d3f5c;
        scrollbar-color: #6c63ff #1a1d2e;
        scrollbar-size: 1 1;
    }
    ChatLog {
        padding: 1 2;
    }

    /* ── Message styles ──────────────────────────────────────── */
    .msg-user {
        color: #e0e0ff;
        border-left: solid #6c63ff;
        background: #12152a;
        padding: 0 1;
        margin-bottom: 1;
    }
    .msg-bot {
        color: #c8ffc8;
        border-left: solid #00cc66;
        background: #0a140a;
        padding: 0 1;
        margin-bottom: 1;
    }
    .msg-sys {
        color: #3d3f5c;
        text-style: italic;
        margin-bottom: 1;
    }
    .msg-error {
        color: #ff6666;
        border-left: solid #cc2222;
        background: #1a0a0a;
        padding: 0 1;
        margin-bottom: 1;
    }
    .msg-help {
        color: #9f99ff;
        border-left: solid #4a44cc;
        background: #0d0f20;
        padding: 0 1;
        margin-bottom: 1;
    }

    /* ── Input area ──────────────────────────────────────────── */
    #input-area {
        height: 5;
        background: #0d0f17;
        border-top: solid #1a1d2e;
        padding: 1 1 0 1;
    }
    #input-row {
        height: 3;
        align: left middle;
    }
    #caret {
        color: #6c63ff;
        width: 4;
        content-align: center middle;
        text-style: bold;
    }
    #prompt {
        width: 1fr;
        background: #12152a;
        border: solid #252850;
        color: #e0e0ff;
        padding: 0 1;
    }
    #prompt:focus {
        border: solid #6c63ff;
        background: #0f1228;
    }

    /* ── Status bar ──────────────────────────────────────────── */
    #status-bar {
        height: 1;
        background: #12152a;
        layout: horizontal;
        padding: 0 1;
    }
    #sb-left  { width: 1fr;  color: #6c63ff; }
    #sb-mid   { width: auto; color: #3d3f5c; content-align: center middle; }
    #sb-right { width: auto; color: #3d3f5c; }

    #btn-provider, #btn-model {
        width: auto;
        min-width: 3;
        height: 1;
        margin: 0 0 0 1;
        background: #1a1d2e;
        color: #6c63ff;
        border: none;
        content-align: center middle;
    }

    #btn-provider:hover, #btn-model:hover {
        background: #6c63ff;
        color: white;
    }

    Footer {
        background: #0d0f17;
        color: #3d3f5c;
    }
    Footer > .footer--highlight { background: #6c63ff; color: white; }
    Footer > .footer--key       { color: #6c63ff; }
    """

    BINDINGS = [
        Binding("ctrl+p", "pick_provider", "Provider"),
        Binding("ctrl+m", "pick_model",    "Model"),
        Binding("ctrl+s", "show_status",   "Status"),
        Binding("ctrl+l", "clear_chat",    "Clear"),
        Binding("ctrl+n", "new_session",   "New"),
        Binding("ctrl+c", "quit",          "Quit"),
    ]

    def __init__(self, cfg: AppConfig) -> None:
        super().__init__()
        self._cfg = cfg
        self._session = ChatSession(provider=cfg.provider, model=cfg.model)
        self._busy = False
        self._history: list[str] = list(cfg.prompt_history)
        self._hist_idx: int = -1

    # ── Composition ───────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Vertical(id="banner-wrap"):
            yield Static(BANNER, id="banner")
            yield Static(
                "Free GPT-4 access · No API key · /help for commands",
                id="banner-sub",
            )

        scroll = ScrollableContainer(ChatLog(id="chat-log"), id="chat-scroll")
        scroll.border_title = " conversation "
        yield scroll

        with Vertical(id="input-area"):
            with Horizontal(id="input-row"):
                yield Label("›", id="caret")
                yield Input(
                    placeholder="Ask anything…  (/help for commands)",
                    id="prompt",
                )

        with Horizontal(id="status-bar"):
            yield Static(self._sb_left(), id="sb-left")
            yield Button("Provider", id="btn-provider")
            yield Static("   GPT4FREE TUI   ", id="sb-mid")
            yield Static("ctrl+p/m/s", id="sb-right")

        yield Footer()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_mount(self) -> None:
        self.query_one("#prompt", Input).focus()
        log = self.query_one(ChatLog)
        log.sys(
            f"🚀  GPT4FREE TUI  ·  provider: [bold]{self._session.provider}[/bold]"
            f"  ·  model: [bold]{self._session.model}[/bold]"
        )
        log.sys("Type [bold]/help[/bold] to see available commands.")

    # ── Input ─────────────────────────────────────────────────────────────────

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text or self._busy:
            return
        event.input.value = ""
        self._hist_idx = -1

        if text.startswith("/"):
            await self._handle_command(text)
        else:
            self._do_chat(text)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-provider":
            await self.action_pick_provider()

    def on_key(self, event: object) -> None:
        from textual.events import Key

        if not isinstance(event, Key):
            return
        inp = self.query_one("#prompt", Input)

        if event.key == "up":
            if self._history:
                self._hist_idx = min(self._hist_idx + 1, len(self._history) - 1)
                inp.value = self._history[-(self._hist_idx + 1)]
                inp.cursor_position = len(inp.value)
        elif event.key == "down":
            if self._hist_idx > 0:
                self._hist_idx -= 1
                inp.value = self._history[-(self._hist_idx + 1)]
                inp.cursor_position = len(inp.value)
            elif self._hist_idx == 0:
                self._hist_idx = -1
                inp.value = ""

    # ── Commands ──────────────────────────────────────────────────────────────

    async def _handle_command(self, cmd: str) -> None:
        log = self.query_one(ChatLog)
        base = cmd.split()[0].lower()

        if base == "/help":
            log.add_widget(Static(HELP_TEXT, classes="msg-help"))

        elif base == "/provider":
            await self.action_pick_provider()

        elif base == "/model":
            await self.action_pick_model()

        elif base == "/status":
            await self.action_show_status()

        elif base in ("/clear", "/c"):
            self.action_clear_chat()

        elif base in ("/new", "/n"):
            self.action_new_session()

        elif base in ("/exit", "/quit", "/q"):
            self.action_quit()

        else:
            log.error(f"Unknown command: {cmd}  — type /help for list")

    # ── Chat worker ───────────────────────────────────────────────────────────

    @work(exclusive=True)
    async def _do_chat(self, text: str) -> None:
        log = self.query_one(ChatLog)
        log.user(text)
        self._session.push_user(text)

        self._history.append(text)
        self._cfg.add_to_history(text)
        self._cfg.provider = self._session.provider
        self._cfg.model = self._session.model
        save_config(self._cfg)

        self._busy = True
        self._refresh_status()

        bot_widget = log.bot_placeholder()
        collected = ""

        try:
            async for chunk in self._session.ask_stream():
                collected += chunk
                log.update_bot(bot_widget, collected)
        except Exception as exc:  # noqa: BLE001
            log.error(str(exc))
        finally:
            self._session.push_assistant(collected)
            self._busy = False
            self._refresh_status()

    # ── Actions ───────────────────────────────────────────────────────────────

    async def action_pick_provider(self) -> None:
        infos = list_providers()

        def _on_pick(name: Optional[str]) -> None:
            if not name:
                return
            self._session.provider = name
            for p in infos:
                if p.name == name and p.model_list:
                    self._session.model = p.model_list[0].alias
                    break
            self._refresh_status()
            log = self.query_one(ChatLog)
            log.sys(
                f"✅  Provider → [bold]{self._session.provider}[/bold]"
                f"  ·  model → [bold]{self._session.model}[/bold]"
            )
            self._cfg.provider = self._session.provider
            self._cfg.model = self._session.model
            save_config(self._cfg)

        await self.push_screen(ProviderPickerScreen(infos), _on_pick)

    async def action_pick_model(self) -> None:
        infos = list_providers()
        model_list = []
        for p in infos:
            if p.name == self._session.provider:
                model_list = p.model_list
                break

        if not model_list:
            self.query_one(ChatLog).error("No models found for current provider.")
            return

        def _on_pick(alias: Optional[str]) -> None:
            if not alias:
                return
            self._session.model = alias
            self._refresh_status()
            self.query_one(ChatLog).sys(f"✅  Model → [bold]{alias}[/bold]")
            self._cfg.model = alias
            save_config(self._cfg)

        await self.push_screen(ModelPickerScreen(model_list), _on_pick)

    async def action_show_status(self) -> None:
        await self.push_screen(StatusScreen())

    def action_clear_chat(self) -> None:
        self._session.clear()
        log = self.query_one(ChatLog)
        log.remove_children()
        log.sys("🗑  Conversation cleared.")

    def action_new_session(self) -> None:
        self._session.clear()
        log = self.query_one(ChatLog)
        log.remove_children()
        log.sys("✨  New session started.")

    def action_quit(self) -> None:
        save_config(self._cfg)
        self.exit()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _sb_left(self) -> str:
        icon = "⟳" if self._busy else "●"
        state = " generating…" if self._busy else " ready"
        return f" {icon} {self._session.provider} / {self._session.model}{state}"

    def _refresh_status(self) -> None:
        self.query_one("#sb-left", Static).update(self._sb_left())
