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
