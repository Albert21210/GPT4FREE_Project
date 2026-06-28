"""
GPT4FREE — Gemini CLI-style TUI and CLI tool.

Usage examples:
  gpt4free                          # launch TUI
  gpt4free -p "Explain recursion"   # one-shot CLI prompt
  gpt4free providers                # list all providers
  gpt4free status                   # probe & display provider status
"""

from __future__ import annotations

import asyncio
import sys
from typing import Annotated, Optional

import typer
from rich.console import Console

console = Console()
app = typer.Typer(
    name="gpt4free",
    help="GPT4FREE — free GPT-4 TUI/CLI · No API key required",
    add_completion=False,
    rich_markup_mode="rich",
)

@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
      prompt: Annotated[
        Optional[str],
        typer.Option(
            "--prompt", "-p",
            help="One-shot prompt (skip TUI, print response and exit)",
        ),
    ] = None,
      provider: Annotated[
        Optional[str],
        typer.Option("--provider", "-P", help="Override provider"),
    ] = None,
      model: Annotated[
        Optional[str],
        typer.Option("--model", "-m", help="Override model"),
    ] = None,
      no_stream: Annotated[
        bool,
        typer.Option("--no-stream", help="Disable streaming (print all at once)"),
    ] = False,
) -> None:
    """Launch TUI, or use [bold]-p[/bold] for a single CLI prompt."""
    if ctx.invoked_subcommand is not None:
        return

    from gpt4free.config import load_config, save_config
    from gpt4free.providers import get_provider_info

    cfg = load_config()
    effective_provider = provider or cfg.provider
    effective_model = model or cfg.model

    if prompt:
        _cli_prompt(
            text=prompt,
            provider=effective_provider,
            model=effective_model,
            stream=not no_stream,
        )

    else:
        from gpt4free.tui.app import GPT4FREETUI

        if provider:
            cfg.provider = provider
        if model:
            cfg.model = model

        GPT4FREETUI(cfg).run()

@app.command("providers")
def cmd_providers(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show all models per provider"),
    ] = False,
) -> None:
    """List all available providers and their models."""
    from rich.table import Table
    from gpt4free.providers import list_providers, STATUS_COLOR, STATUS_EMOJI

    infos = list_providers()
    table = Table(
        title="[bold #6c63ff]GPT4FREE — Providers[/bold #6c63ff]",
        border_style="#1a1d2e",
        header_style="bold #6c63ff",
        show_lines=True,
    )
