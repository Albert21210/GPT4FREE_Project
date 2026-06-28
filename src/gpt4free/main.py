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
    table.add_column("Provider", style="bold white", min_width=14)
    table.add_column("Status", min_width=12)
    table.add_column("# Models", justify="right", min_width=8)
    table.add_column("Models", min_width=50 if verbose else 40)

    for p in infos:
        emoji = STATUS_EMOJI.get(p.status, "?")
        color = STATUS_COLOR.get(p.status, "white")
        if verbose:
            preview = "\n".join(f"  {m.display} [{m.alias}]" for m in p.model_list)
        else:
            preview = ", ".join(m.display for m in p.model_list[:4])
            if len(p.model_list) > 4:
                preview += f" +{len(p.model_list) - 4}"
        table.add_row(
            p.name,
            f"[{color}]{emoji} {p.status.value}[/{color}]",
            str(len(p.model_list)),
            preview,
        )

    console.print(table)

@app.command("status")
def cmd_status(
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Probe timeout per provider (seconds)"),
    ] = 12.0,
) -> None:
    """Probe all providers and display live status."""
    from gpt4free.providers import list_providers, probe_all, PROBE_TIMEOUT
    import gpt4free.providers as prov_mod

    prov_mod.PROBE_TIMEOUT = timeout
    providers = list_providers()

    with console.status(
        "[bold #6c63ff]Probing providers…[/bold #6c63ff]",
        spinner="dots",
    ):
        results = asyncio.run(probe_all(providers))

    from gpt4free.render import render_provider_table

    render_provider_table(results)

@app.command("config")
def cmd_config(
    show: Annotated[bool, typer.Option("--show", help="Print current config")] = False,
    provider: Annotated[Optional[str], typer.Option("--provider", "-P")] = None,
    model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
) -> None:
    """View or update saved configuration."""
    from gpt4free.config import load_config, save_config
    import json

    cfg = load_config()

    if provider:
        cfg.provider = provider
        save_config(cfg)
        console.print(f"[green]✓[/green] Provider set to [bold]{provider}[/bold]")

    if model:
        cfg.model = model
        save_config(cfg)
        console.print(f"[green]✓[/green] Model set to [bold]{model}[/bold]")

    if show or (not provider and not model):
        console.print_json(json.dumps(cfg.to_dict(), indent=2))

def _cli_prompt(
    text: str,
    provider: str,
    model: str,
    stream: bool,
) -> None:
    """Run a single prompt in the terminal with streaming output."""
    from gpt4free.chat import ChatSession
    from gpt4free.render import (
        render_assistant_header,
        render_markdown,
        render_stream_chunk,
        render_user_prompt,
    )

    render_user_prompt(text)
    render_assistant_header(provider, model)

    session = ChatSession(provider=provider, model=model)
    session.push_user(text)
