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
