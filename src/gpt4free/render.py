"""Rich-based markdown and syntax rendering for terminal output."""

from __future__ import annotations

import re
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text

_console = Console()

def render_markdown(text: str, theme: str = "monokai") -> None:
    """Render Markdown text with syntax-highlighted code blocks to stdout."""
    pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    last = 0
    parts: list[tuple[str, Optional[str], Optional[str]]] = []

    for m in pattern.finditer(text):
        before = text[last : m.start()]
        if before.strip():
            parts.append((before, None, None))
        lang = m.group(1) or "text"
        code = m.group(2)
        parts.append(("", lang, code))
        last = m.end()

    tail = text[last:]
    if tail.strip():
        parts.append((tail, None, None))

    for content, lang, code in parts:
        if lang is not None and code is not None:
            syntax = Syntax(
                code.rstrip(),
                lang,
                theme=theme,
                line_numbers=True,
                word_wrap=True,
            )
            _console.print(syntax)
        else:
            _console.print(Markdown(content))

def render_stream_chunk(chunk: str) -> None:
    """Print a raw streaming chunk without newline."""
    _console.print(chunk, end="", highlight=False)

def render_user_prompt(text: str) -> None:
    """Print the echoed user prompt."""
    _console.print(f"[bold #6c63ff]You ‚Äļ[/bold #6c63ff] {text}")

def render_assistant_header(provider: str, model: str) -> None:
    """Print the assistant label line."""
    _console.print(
        f"\n[bold #00cc66]GPT4FREE[/bold #00cc66] "
        f"[dim]({provider} / {model})[/dim]"
    )

def render_system(text: str) -> None:
    """Print a dim system/info message."""
    _console.print(f"[dim]{text}[/dim]")

def render_error(text: str) -> None:
    """Print an error message."""
    _console.print(f"[bold red]Error:[/bold red] {text}")

def render_banner() -> None:
    """Print the GPT4FREE ASCII banner."""
    banner = """[bold #6c63ff]
  ██████╗ ██████╗ ████████╗██╗  ██╗███████╗██████╗ ███████╗███████╗
 ██╔════╝ ██╔══██╗╚══██╔══╝██║  ██║██╔════╝██╔══██╗██╔════╝██╔════╝
 ██║  ███╗██████╔╝   ██║   ███████║█████╗  ██████╔╝█████╗  █████╗
 ██║   ██║██╔═══╝    ██║   ╚════██║██╔══╝  ██╔══██╗██╔══╝  ██╔══╝
 ╚██████╔╝██║        ██║        ██║██║     ██║  ██║███████╗███████╗
  ╚═════╝ ╚═╝        ╚═╝        ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝[/bold #6c63ff]"""
    _console.print(banner)
    _console.print(
        "[dim]  Free GPT-4 access ¬∑ No API key ¬∑ "
        "Type [bold]/help[/bold] for commands[/dim]\n"
    )

def render_provider_table(providers: list[object]) -> None:  # ProviderInfo
    """Print a Rich table of all providers and their status."""
    from rich.table import Table
    from gpt4free.providers import ProviderInfo, STATUS_COLOR, STATUS_EMOJI

    table = Table(
        title="[bold #6c63ff]GPT4FREE ‚ÄĒ Provider Status[/bold #6c63ff]",
        border_style="#1e1e3a",
        header_style="bold #6c63ff",
        show_lines=True,
    )
    table.add_column("Provider", style="bold white", min_width=14)
    table.add_column("Status", min_width=14)
    table.add_column("Latency", justify="right", min_width=8)
    table.add_column("Models", min_width=40)

    for p in providers:
        assert isinstance(p, ProviderInfo)
        emoji = STATUS_EMOJI.get(p.status, "?")
        color = STATUS_COLOR.get(p.status, "white")
        lat = f"{p.latency_ms}ms" if p.latency_ms is not None else "‚ÄĒ"
        preview = ", ".join(m.display for m in p.model_list[:4])
        if len(p.model_list) > 4:
            preview += f" +{len(p.model_list) - 4}"
        table.add_row(
            p.name,
            f"[{color}]{emoji} {p.status.value}[/{color}]",
            lat,
            preview,
        )
