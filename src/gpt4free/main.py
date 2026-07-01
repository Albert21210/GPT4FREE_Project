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
            api_keys=cfg.api_keys,
            custom_providers=cfg.custom_providers,
            proxy=cfg.proxy,
            force_proxy=cfg.force_proxy,
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
    from gpt4free.config import load_config
    from gpt4free.providers import list_providers, STATUS_COLOR, STATUS_EMOJI

    cfg = load_config()
    infos = list_providers(cfg.custom_providers)
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

@app.command("models")
def cmd_models(
    provider: Annotated[
        str,
        typer.Argument(help="Provider name, e.g. PollinationsAI, DeepInfra, Groq"),
    ],
) -> None:
    """Fetch the LIVE model catalog for a provider straight from its API.

    `providers`/`status` only show a small curated subset we verified by
    hand. Most provider classes in g4f can report their full current model
    list (sometimes 100+ entries, see g4f.dev/docs/providers-and-models) —
    this command asks the provider directly instead of relying on our list.
    Nothing validates -m/--model against the curated list, so any id printed
    here can be used right away: gpt4free -P <provider> -m "<model id>"
    """
    import asyncio
    from gpt4free.config import load_config
    from gpt4free.providers import fetch_live_models, get_provider_info

    cfg = load_config()
    info = get_provider_info(provider, cfg.custom_providers)
    if info is None:
        console.print(f"[red]✗[/red] Unknown provider [bold]{provider}[/bold]. "
                       f"Run `gpt4free providers` to see available names.")
        raise typer.Exit(code=1)

    api_key = cfg.get_api_key(provider)
    with console.status(f"[dim]Asking {provider} for its live model list…[/dim]"):
        models = asyncio.run(fetch_live_models(provider, api_key=api_key))

    if not models:
        console.print(
            f"[yellow]![/yellow] {provider} didn't return a live model list "
            f"(no get_models() support, or the request failed/timed out). "
            f"Falling back to the curated list from `providers`:"
        )
        for m in info.model_list:
            console.print(f"  {m.display} [dim][{m.alias}][/dim]")
        return

    console.print(f"[green]✓[/green] {provider} reports [bold]{len(models)}[/bold] live model(s):")
    for m in models:
        console.print(f"  {m.alias}")
    console.print(
        f"\n[dim]Use any of these right away: "
        f"gpt4free -P {provider} -m \"<model id>\"[/dim]"
    )
