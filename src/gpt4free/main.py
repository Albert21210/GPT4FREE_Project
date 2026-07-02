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

@app.command("status")
def cmd_status(
    timeout: Annotated[
        float,
        typer.Option("--timeout", "-t", help="Probe timeout per provider (seconds)"),
    ] = 12.0,
) -> None:
    """Probe all providers and display live status."""
    import os
    from gpt4free.config import load_config
    from gpt4free.providers import list_providers, probe_all, PROBE_TIMEOUT
    import gpt4free.providers as prov_mod

    prov_mod.PROBE_TIMEOUT = timeout
    cfg = load_config()
    providers = list_providers(cfg.custom_providers)
    proxy = os.environ.get("G4F_PROXY") or cfg.proxy or None

    with console.status(
        "[bold #6c63ff]Probing providers…[/bold #6c63ff]",
        spinner="dots",
    ):
        results = asyncio.run(probe_all(providers, proxy=proxy, api_keys=cfg.api_keys))

    from gpt4free.render import render_provider_table

    render_provider_table(results)

@app.command("config")
def cmd_config(
    show: Annotated[bool, typer.Option("--show", help="Print current config")] = False,
    provider: Annotated[Optional[str], typer.Option("--provider", "-P")] = None,
    model: Annotated[Optional[str], typer.Option("--model", "-m")] = None,
    proxy: Annotated[
        Optional[str],
        typer.Option("--proxy", help="Set outbound proxy, e.g. socks5://127.0.0.1:1080"),
    ] = None,
    force_proxy: Annotated[
        bool,
        typer.Option("--force-proxy", help="Route ALL providers through the proxy, not just geoblocked ones"),
    ] = False,
    clear_proxy: Annotated[
        bool,
        typer.Option("--clear-proxy", help="Remove the configured proxy"),
    ] = False,
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

    if clear_proxy:
        cfg.clear_proxy()
        save_config(cfg)
        console.print("[green]✓[/green] Proxy cleared")

    if proxy:
        cfg.set_proxy(proxy, force=force_proxy)
        save_config(cfg)
        scope = "ALL providers" if force_proxy else "geoblocked providers only"
        console.print(f"[green]✓[/green] Proxy set to [bold]{proxy}[/bold]  ·  scope: {scope}")

    if show or (not provider and not model and not proxy and not clear_proxy):
        console.print_json(json.dumps(cfg.to_dict(), indent=2))

@app.command("keys")
def cmd_keys(
    set_: Annotated[
        Optional[str],
        typer.Option(
            "--set",
            help='Set a key as "ProviderName=sk-...", e.g. --set "Cerebras=sk-abc123"',
        ),
    ] = None,
    remove: Annotated[
        Optional[str],
        typer.Option("--remove", help="Remove the key for this provider name"),
    ] = None,
    show: Annotated[
        bool,
        typer.Option("--show", help="List configured providers and whether a key is set (keys themselves are masked)"),
    ] = False,
) -> None:
    """Manage manual API keys for built-in providers (e.g. Cerebras, Gemini, Grok).

    These unlock providers that otherwise come back auth_required in `status`.
    Keys are stored locally in your config file, never sent anywhere except
    directly to that provider's API.
    """
    from gpt4free.config import load_config, save_config
    from gpt4free.providers import list_providers

    cfg = load_config()

    if set_:
        if "=" not in set_:
            console.print('[red]✗[/red] Expected format: --set "ProviderName=your-key"')
            raise typer.Exit(code=1)
        name, _, key = set_.partition("=")
        name, key = name.strip(), key.strip()
        if not key:
            console.print("[red]✗[/red] Key cannot be empty")
            raise typer.Exit(code=1)
        cfg.set_api_key(name, key)
        save_config(cfg)
        console.print(f"[green]✓[/green] Key set for [bold]{name}[/bold]")
        return

    if remove:
        cfg.set_api_key(remove, "")
        save_config(cfg)
        console.print(f"[green]✓[/green] Key removed for [bold]{remove}[/bold]")
        return
    known = {p.name for p in list_providers(cfg.custom_providers)}
    known |= set(cfg.api_keys)
    if not known:
        console.print("No providers found.")
        return
    from rich.table import Table
    tbl = Table()
    tbl.add_column("Provider")
    tbl.add_column("Key set")
    for name in sorted(known):
        has_key = "[green]yes[/green]" if cfg.get_api_key(name) else "[dim]no[/dim]"
        tbl.add_row(name, has_key)
    console.print(tbl)

@app.command("custom-providers")
def cmd_custom_providers(
    add: Annotated[
        Optional[str],
        typer.Option(
            "--add",
            help='Add as "Name=https://base.url/v1", e.g. --add "MyServer=http://localhost:8000/v1"',
        ),
    ] = None,
    models: Annotated[
        Optional[str],
        typer.Option(
            "--models",
            help='Comma-separated model aliases to register with --add, e.g. --models "llama3,mixtral"',
        ),
    ] = None,
    api_key: Annotated[
        Optional[str],
        typer.Option("--api-key", help="API key to send to this custom endpoint, if it needs one"),
    ] = None,
    remove: Annotated[
        Optional[str],
        typer.Option("--remove", help="Remove a custom provider by name"),
    ] = None,
    show: Annotated[
        bool,
        typer.Option("--show", help="List configured custom providers"),
    ] = False,
) -> None:
    """Manually register your own OpenAI-compatible provider and its models.

    Example:
      gpt4free custom-providers --add "MyServer=http://localhost:8000/v1" --models "llama3,mixtral"
      gpt4free custom-providers --add "Together=https://api.together.xyz/v1" --models "meta-llama/Llama-3-70b" --api-key sk-...
    """
    from gpt4free.config import load_config, save_config

    cfg = load_config()

    if add:
        if "=" not in add:
            console.print('[red]✗[/red] Expected format: --add "Name=https://base.url/v1"')
            raise typer.Exit(code=1)
        name, _, base_url = add.partition("=")
        name, base_url = name.strip(), base_url.strip()
        if not base_url:
            console.print("[red]✗[/red] base_url cannot be empty")
            raise typer.Exit(code=1)
        if not models:
            console.print('[red]✗[/red] --models is required, e.g. --models "llama3,mixtral"')
            raise typer.Exit(code=1)
        model_list = [
            {"alias": m.strip(), "display": m.strip()}
            for m in models.split(",") if m.strip()
        ]
        cfg.add_custom_provider(name, base_url, model_list, api_key=api_key or "")
        save_config(cfg)
        console.print(f"[green]✓[/green] Custom provider [bold]{name}[/bold] added "
                      f"({len(model_list)} model(s)) → {base_url}")
        return

    if remove:
        cfg.remove_custom_provider(remove)
        save_config(cfg)
        console.print(f"[green]✓[/green] Custom provider [bold]{remove}[/bold] removed")
        return

    if not cfg.custom_providers:
        console.print("No custom providers configured. Use --add to register one.")
        return
    from rich.table import Table
    tbl = Table()
    tbl.add_column("Name")
    tbl.add_column("Base URL")
    tbl.add_column("Key set")
    tbl.add_column("Models")
    for name, c in cfg.custom_providers.items():
        model_names = ", ".join(m["alias"] for m in c.get("models", []))
        tbl.add_row(
            name,
            c.get("base_url", ""),
            "[green]yes[/green]" if c.get("api_key") else "[dim]no[/dim]",
            model_names,
        )
    console.print(tbl)

@app.command("mcp")
def cmd_mcp(
    add: Annotated[
        Optional[str],
        typer.Option(
            "--add",
            help='Add as "Name=command arg1 arg2", e.g. --add "files=npx -y @modelcontextprotocol/server-filesystem /home/me"',
        ),
    ] = None,
    remove: Annotated[
        Optional[str],
        typer.Option("--remove", help="Remove an MCP server by name"),
    ] = None,
    enable: Annotated[
        Optional[str],
        typer.Option("--enable", help="Enable a previously-added MCP server"),
    ] = None,
    disable: Annotated[
        Optional[str],
        typer.Option("--disable", help="Disable an MCP server without removing it"),
    ] = None,
    show: Annotated[
        bool,
        typer.Option("--show", help="List configured MCP servers"),
    ] = False,
) -> None:
    """Manage local MCP (Model Context Protocol) servers.

    Each server is launched as a subprocess over stdio and its tools become
    available to the model automatically in both the TUI and `-p` prompts.

    Example:
      gpt4free mcp --add "files=npx -y @modelcontextprotocol/server-filesystem /home/me/projects"
      gpt4free mcp --disable files
      gpt4free mcp --show
    """
    import shlex

    from gpt4free.config import load_config, save_config
    from gpt4free.mcp_client import MCP_AVAILABLE

    cfg = load_config()

    if add:
        if "=" not in add:
            console.print('[red]✗[/red] Expected format: --add "Name=command arg1 arg2"')
            raise typer.Exit(code=1)
        name, _, command_line = add.partition("=")
        name, command_line = name.strip(), command_line.strip()
        parts = shlex.split(command_line)
        if not parts:
            console.print("[red]✗[/red] Command cannot be empty")
            raise typer.Exit(code=1)
        cfg.add_mcp_server(name, command=parts[0], args=parts[1:])
        save_config(cfg)
        console.print(f"[green]✓[/green] MCP server [bold]{name}[/bold] added → {command_line}")
        if not MCP_AVAILABLE:
            console.print("[yellow]![/yellow] The 'mcp' package isn't installed yet: pip install mcp")
        return

    if remove:
        cfg.remove_mcp_server(remove)
        save_config(cfg)
        console.print(f"[green]✓[/green] MCP server [bold]{remove}[/bold] removed")
        return

    if enable:
        cfg.set_mcp_server_enabled(enable, True)
        save_config(cfg)
        console.print(f"[green]✓[/green] MCP server [bold]{enable}[/bold] enabled")
        return

    if disable:
        cfg.set_mcp_server_enabled(disable, False)
        save_config(cfg)
        console.print(f"[green]✓[/green] MCP server [bold]{disable}[/bold] disabled")
        return

    if not cfg.mcp_servers:
        console.print("No MCP servers configured. Use --add to register one.")
        return
    from rich.table import Table
    tbl = Table()
    tbl.add_column("Name")
    tbl.add_column("Command")
    tbl.add_column("Enabled")
    for name, s in cfg.mcp_servers.items():
        cmd = " ".join([s.get("command", "")] + s.get("args", []))
        tbl.add_row(name, cmd, "[green]yes[/green]" if s.get("enabled", True) else "[dim]no[/dim]")
    console.print(tbl)
    if not MCP_AVAILABLE:
        console.print("\n[yellow]![/yellow] The 'mcp' package isn't installed: pip install mcp")

@app.command("tools")
def cmd_tools(
    test: Annotated[
        bool,
        typer.Option("--test", help="Actually connect to every enabled MCP server and list its live tools"),
    ] = False,
) -> None:
    """Show which tools the model can call: built-in skills + configured MCP servers."""
    from gpt4free.config import load_config
    from gpt4free.skills import build_default_registry

    cfg = load_config()

    console.print("[bold #6c63ff]Built-in tools[/bold #6c63ff] "
                  f"({'enabled' if cfg.builtin_tools_enabled else '[dim]disabled[/dim]'})")
    if cfg.builtin_tools_enabled:
        for t in build_default_registry().list_tools():
            console.print(f"  • [bold]{t.name}[/bold] — {t.description}")

    if not cfg.mcp_servers:
        console.print("\n[dim]No MCP servers configured. Use `gpt4free mcp --add ...`.[/dim]")
        return

    console.print("\n[bold #6c63ff]MCP servers[/bold #6c63ff]")
    if not test:
        for name, s in cfg.mcp_servers.items():
            status = "[green]enabled[/green]" if s.get("enabled", True) else "[dim]disabled[/dim]"
            console.print(f"  • [bold]{name}[/bold] ({status}) — run with [dim]--test[/dim] to list its live tools")
        return

    import asyncio as _asyncio
    from contextlib import AsyncExitStack

    from gpt4free.tools_setup import build_tool_registry

    async def _probe() -> None:
        async with AsyncExitStack() as stack:

            def _on_error(name: str, msg: str) -> None:
                console.print(f"  • [bold]{name}[/bold] — [red]failed:[/red] {msg}")

            registry = await build_tool_registry(cfg, stack, on_error=_on_error)
            builtin_names = {t.name for t in build_default_registry().list_tools()} if cfg.builtin_tools_enabled else set()
            mcp_tools = [t for t in registry.list_tools() if t.name not in builtin_names]
            if not mcp_tools:
                console.print("  [dim](no tools discovered)[/dim]")
            for t in mcp_tools:
                console.print(f"  • [bold]{t.name}[/bold] — {t.description}")

    with console.status("[dim]Connecting to MCP servers…[/dim]", spinner="dots"):
        _asyncio.run(_probe())

def _cli_prompt(
    text: str,
    provider: str,
    model: str,
    stream: bool,
    api_keys: Optional[dict[str, str]] = None,
    custom_providers: Optional[dict[str, dict]] = None,
    proxy: Optional[str] = None,
    force_proxy: bool = False,
) -> None:
    """Run a single prompt in the terminal with streaming output."""
    from contextlib import AsyncExitStack

    from gpt4free.chat import ChatSession
    from gpt4free.config import load_config
    from gpt4free.render import (
        render_assistant_header,
        render_markdown,
        render_stream_chunk,
        render_user_prompt,
    )
    from gpt4free.tools_setup import build_tool_registry

    render_user_prompt(text)
    render_assistant_header(provider, model)

    session = ChatSession(
        provider=provider,
        model=model,
        api_keys=api_keys or {},
        custom_providers=custom_providers or {},
        proxy=proxy,
        force_proxy=force_proxy,
    )
    session.push_user(text)

    cfg = load_config()

    async def _run() -> str:
        async with AsyncExitStack() as stack:

            def _on_error(name: str, msg: str) -> None:
                console.print(f"[yellow]![/yellow] MCP server [bold]{name}[/bold] unavailable: {msg}")

            session.tools = await build_tool_registry(cfg, stack, on_error=_on_error)

            if len(session.tools) > 0:
                # Function-calling requires the full round-trip (model → tool
                # → model), so this path is never streamed token-by-token.
                with console.status("[dim]Thinking (tools enabled)…[/dim]", spinner="dots"):
                    return await session.ask_with_tools()

            if stream:
                collected = ""
                async for chunk in session.ask_stream():
                    render_stream_chunk(chunk)
                    collected += chunk
                console.print()
                return collected

            with console.status("[dim]Thinking…[/dim]", spinner="dots"):
                return await session.ask_once()

    reply = asyncio.run(_run())
    render_markdown(reply)
