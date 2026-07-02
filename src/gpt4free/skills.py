"""Built-in local skills — tools available out of the box, no MCP server needed.

These are plain Python functions registered into a `ToolRegistry` via the
`@registry.skill(...)` decorator, exactly the same mechanism used for MCP
tools. `build_default_registry()` returns a fresh registry with all of them
already registered; callers (CLI / TUI) can register more MCP tools into it
afterwards.
"""

from __future__ import annotations

import ast
import operator
from datetime import datetime
from pathlib import Path
from typing import Any

from gpt4free.tools import ToolRegistry

# calculator: safe arithmetic evaluation (no eval())

_ALLOWED_BINOPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARYOPS: dict[type, Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


class UnsafeExpressionError(ValueError):
    pass


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise UnsafeExpressionError(f"unsupported constant: {node.value!r}")
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_eval_node(node.operand))
    raise UnsafeExpressionError(f"unsupported expression: {ast.dump(node)}")


def safe_eval_expression(expression: str) -> float:
    """Evaluate a numeric expression using only +-*/%** and parens. Never
    uses Python's `eval`, so it can't execute arbitrary code."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpressionError(f"invalid expression: {exc}") from exc
    return _eval_node(tree.body)


def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression, e.g. "12 * (3 + 4) / 2"."""
    try:
        result = safe_eval_expression(expression)
    except UnsafeExpressionError as exc:
        return f"error: {exc}"
    except ZeroDivisionError:
        return "error: division by zero"
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return str(result)


# current_datetime

def current_datetime() -> str:
    """Return the current local date and time."""
    now = datetime.now()
    return now.strftime("%A, %Y-%m-%d %H:%M:%S")


# read_text_file: read a local text file, bounded so a huge file can't blow
# up the model's context window.

MAX_READ_CHARS = 20_000


def read_text_file(path: str, max_chars: int = MAX_READ_CHARS) -> str:
    """Read a local text file (relative to the current working directory
    unless an absolute path is given) and return up to `max_chars` characters."""
    try:
        p = Path(path).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists():
            return f"error: file not found: {path}"
        if not p.is_file():
            return f"error: not a file: {path}"
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"

    capped = min(max_chars, MAX_READ_CHARS)
    if len(text) > capped:
        return text[:capped] + f"\n... [truncated, {len(text) - capped} more characters]"
    return text


# list_directory

MAX_LIST_ENTRIES = 200


def list_directory(path: str = ".") -> str:
    """List files and subdirectories in a local directory."""
    try:
        p = Path(path).expanduser()
        if not p.is_absolute():
            p = Path.cwd() / p
        if not p.exists():
            return f"error: path not found: {path}"
        if not p.is_dir():
            return f"error: not a directory: {path}"
        entries = sorted(p.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"

    lines = [f"{'📁' if e.is_dir() else '📄'} {e.name}" for e in entries[:MAX_LIST_ENTRIES]]
    if len(entries) > MAX_LIST_ENTRIES:
        lines.append(f"... [{len(entries) - MAX_LIST_ENTRIES} more entries]")
    return "\n".join(lines) if lines else "(empty directory)"


def build_default_registry() -> ToolRegistry:
    """Build a ToolRegistry with all built-in local skills registered."""
    registry = ToolRegistry()

    registry.skill(
        "calculator",
        "Evaluate a basic arithmetic expression (+ - * / % ** and parens). "
        "Use this instead of doing math yourself.",
        {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "e.g. '(3 + 4) * 2'"}},
            "required": ["expression"],
        },
    )(calculator)

    registry.skill(
        "current_datetime",
        "Get the current local date and time.",
        {"type": "object", "properties": {}},
    )(current_datetime)

    registry.skill(
        "read_text_file",
        "Read the contents of a local text file on the user's machine.",
        {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path, absolute or relative to the cwd"},
                "max_chars": {"type": "integer", "description": "Max characters to return"},
            },
            "required": ["path"],
        },
    )(read_text_file)

    registry.skill(
        "list_directory",
        "List files and subdirectories in a local directory on the user's machine.",
        {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Directory path, defaults to cwd"}},
        },
    )(list_directory)

    return registry
