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

class TestKeysCommand:
    def test_show_empty_by_default(self, isolated_config) -> None:
        result = runner.invoke(app, ["keys", "--show"])
        assert result.exit_code == 0
        assert "Provider" in result.stdout

    def test_set_requires_equals_sign(self, isolated_config) -> None:
        result = runner.invoke(app, ["keys", "--set", "Cerebras-no-equals"])
        assert result.exit_code != 0

    def test_set_rejects_empty_key(self, isolated_config) -> None:
        result = runner.invoke(app, ["keys", "--set", "Cerebras="])
        assert result.exit_code != 0

    def test_set_and_show_key(self, isolated_config) -> None:
        set_result = runner.invoke(app, ["keys", "--set", "Cerebras=sk-test123"])
        assert set_result.exit_code == 0
        assert "Cerebras" in set_result.stdout

        show_result = runner.invoke(app, ["keys", "--show"])
        assert show_result.exit_code == 0
        assert "Cerebras" in show_result.stdout
        assert "sk-test123" not in show_result.stdout

    def test_remove_key(self, isolated_config) -> None:
        runner.invoke(app, ["keys", "--set", "Cerebras=sk-test123"])
        remove_result = runner.invoke(app, ["keys", "--remove", "Cerebras"])
        assert remove_result.exit_code == 0

        from gpt4free.config import load_config
        cfg = load_config()
        assert cfg.get_api_key("Cerebras") is None

    def test_key_persists_across_loads(self, isolated_config) -> None:
        runner.invoke(app, ["keys", "--set", "Gemini=sk-abc"])

        from gpt4free.config import load_config
        cfg = load_config()
        assert cfg.get_api_key("Gemini") == "sk-abc"

class TestCustomProvidersCommand:
    def test_show_empty_by_default(self, isolated_config) -> None:
        result = runner.invoke(app, ["custom-providers", "--show"])
        assert result.exit_code == 0
        assert "No custom providers" in result.stdout

    def test_add_requires_equals_sign(self, isolated_config) -> None:
        result = runner.invoke(app, ["custom-providers", "--add", "BadFormat", "--models", "m1"])
        assert result.exit_code != 0

    def test_add_requires_models(self, isolated_config) -> None:
        result = runner.invoke(
            app, ["custom-providers", "--add", "MyServer=http://localhost:8000/v1"]
        )
        assert result.exit_code != 0

    def test_add_and_show(self, isolated_config) -> None:
        add_result = runner.invoke(
            app,
            [
                "custom-providers", "--add", "MyServer=http://localhost:8000/v1",
                "--models", "llama3,mixtral",
            ],
        )
        assert add_result.exit_code == 0
        assert "MyServer" in add_result.stdout

        show_result = runner.invoke(app, ["custom-providers", "--show"])
        assert show_result.exit_code == 0
        assert "MyServer" in show_result.stdout
        assert "llama3" in show_result.stdout
        assert "mixtral" in show_result.stdout

    def test_add_with_api_key_masks_it_in_show(self, isolated_config) -> None:
        runner.invoke(
            app,
            [
                "custom-providers", "--add", "Together=https://api.together.xyz/v1",
                "--models", "m1", "--api-key", "sk-secret",
            ],
        )
        show_result = runner.invoke(app, ["custom-providers", "--show"])
        assert "yes" in show_result.stdout  # key-set indicator
        assert "sk-secret" not in show_result.stdout

    def test_remove(self, isolated_config) -> None:
        runner.invoke(
            app,
            ["custom-providers", "--add", "MyServer=http://localhost:8000/v1", "--models", "llama3"],
        )
        remove_result = runner.invoke(app, ["custom-providers", "--remove", "MyServer"])
        assert remove_result.exit_code == 0

        from gpt4free.config import load_config
        cfg = load_config()
        assert "MyServer" not in cfg.custom_providers

    def test_added_provider_appears_in_providers_list(self, isolated_config) -> None:
        runner.invoke(
            app,
            ["custom-providers", "--add", "MyServer=http://localhost:8000/v1", "--models", "llama3"],
        )
        result = runner.invoke(app, ["providers"])
        assert result.exit_code == 0
        assert "MyServer" in result.stdout

    def test_model_list_parsing_strips_whitespace(self, isolated_config) -> None:
        runner.invoke(
            app,
            [
                "custom-providers", "--add", "MyServer=http://localhost:8000/v1",
                "--models", " llama3 , mixtral ,  ",
            ],
        )
        from gpt4free.config import load_config
        cfg = load_config()
        aliases = [m["alias"] for m in cfg.custom_providers["MyServer"]["models"]]
        assert aliases == ["llama3", "mixtral"]
