"""Tests for gpt4free.skills — built-in local tools."""

from __future__ import annotations

import pytest

from gpt4free.skills import (
    build_default_registry,
    calculator,
    current_datetime,
    list_directory,
    read_text_file,
    safe_eval_expression,
)


# calculator / safe_eval_expression

def test_safe_eval_basic_arithmetic() -> None:
    assert safe_eval_expression("2 + 3") == 5
    assert safe_eval_expression("(3 + 4) * 2") == 14
    assert safe_eval_expression("10 / 4") == 2.5
    assert safe_eval_expression("2 ** 10") == 1024


def test_calculator_returns_string() -> None:
    assert calculator("2 + 2") == "4"
    assert calculator("7 / 2") == "3.5"


def test_calculator_rejects_non_numeric_code() -> None:
    # No eval() under the hood: function calls, names, attribute access, etc.
    # must all be rejected rather than executed.
    result = calculator("__import__('os').system('echo hi')")
    assert result.startswith("error")


def test_calculator_rejects_name_lookup() -> None:
    result = calculator("open('/etc/passwd').read()")
    assert result.startswith("error")


def test_calculator_division_by_zero() -> None:
    assert calculator("1 / 0") == "error: division by zero"


def test_calculator_invalid_syntax() -> None:
    result = calculator("2 +")
    assert result.startswith("error")


# current_datetime

def test_current_datetime_format() -> None:
    result = current_datetime()
    assert isinstance(result, str)
    assert len(result) > 0


# read_text_file

def test_read_text_file_success(tmp_path) -> None:
    f = tmp_path / "hello.txt"
    f.write_text("hello world")
    assert read_text_file(str(f)) == "hello world"


def test_read_text_file_missing() -> None:
    result = read_text_file("/definitely/does/not/exist.txt")
    assert result.startswith("error")


def test_read_text_file_truncates(tmp_path) -> None:
    f = tmp_path / "big.txt"
    f.write_text("x" * 100)
    result = read_text_file(str(f), max_chars=10)
    assert result.startswith("x" * 10)
    assert "truncated" in result


def test_read_text_file_rejects_directory(tmp_path) -> None:
    result = read_text_file(str(tmp_path))
    assert result.startswith("error")


# list_directory

def test_list_directory_success(tmp_path) -> None:
    (tmp_path / "a.txt").write_text("")
    (tmp_path / "sub").mkdir()
    result = list_directory(str(tmp_path))
    assert "a.txt" in result
    assert "sub" in result


def test_list_directory_missing() -> None:
    result = list_directory("/definitely/does/not/exist")
    assert result.startswith("error")


def test_list_directory_empty(tmp_path) -> None:
    assert list_directory(str(tmp_path)) == "(empty directory)"


# build_default_registry

def test_build_default_registry_has_all_skills() -> None:
    registry = build_default_registry()
    names = {t.name for t in registry.list_tools()}
    assert names == {"calculator", "current_datetime", "read_text_file", "list_directory"}


@pytest.mark.asyncio
async def test_build_default_registry_tools_are_callable() -> None:
    registry = build_default_registry()
    result = await registry.execute("calculator", {"expression": "6 * 7"})
    assert result == "42"
