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
