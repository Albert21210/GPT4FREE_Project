"""Tests for the `gpt4free keys` and `gpt4free custom-providers` CLI commands."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from gpt4free.main import app

runner = CliRunner()

@pytest.fixture
def isolated_config(tmp_path):
    """Point the config manager at a throwaway directory for each test."""
    with patch("gpt4free.config.user_config_dir", return_value=str(tmp_path)):
        yield tmp_path
