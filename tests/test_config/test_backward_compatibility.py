from __future__ import annotations
from unittest.mock import patch
import json
from gpt4free.config import AppConfig, load_config, save_config
from gpt4free.providers import DEFAULT_PROVIDER


class TestBackwardCompatibility:

    def test_load_config_compat(self, tmp_path):
        config_dir = tmp_path / "gpt4free-tui"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("gpt4free.config.config_manager.user_config_dir", return_value=str(tmp_path)):
            cfg = AppConfig(provider="PollinationsAI", model="openai")
            save_config(cfg)

            loaded = load_config()
            assert loaded.provider == "PollinationsAI"
            assert loaded.model == "openai"

    def test_load_missing_file_compat(self, tmp_path):
        with patch("gpt4free.config.config_manager.user_config_dir", return_value=str(tmp_path)):
            cfg = load_config()
        assert cfg.provider == DEFAULT_PROVIDER

    def test_load_corrupt_file_compat(self, tmp_path):
        config_dir = tmp_path / "gpt4free-tui"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.json"
        config_path.write_text("{ this is not json }", encoding="utf-8")

        with patch("gpt4free.config.config_manager.user_config_dir", return_value=str(tmp_path)):
            cfg = load_config()
        assert cfg.provider == DEFAULT_PROVIDER
