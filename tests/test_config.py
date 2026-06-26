from __future__ import annotations
from unittest.mock import patch
import pytest
from gpt4free.config import AppConfig, ConfigManager, load_config, save_config
from gpt4free.providers import DEFAULT_MODEL, DEFAULT_PROVIDER


class TestAppConfig:

    def test_defaults(self):
        cfg = AppConfig()
        assert cfg.provider == DEFAULT_PROVIDER
        assert cfg.model == DEFAULT_MODEL
        assert cfg.stream is True
        assert cfg.prompt_history == []
        assert cfg.stats["total_queries"] == 0
        assert cfg.version == "2.0.0"

    def test_history_append(self):
        cfg = AppConfig()
        cfg.add_to_history("hello")
        cfg.add_to_history("world")
        assert cfg.prompt_history == ["hello", "world"]

    def test_history_dedup(self):
        cfg = AppConfig()
        cfg.add_to_history("same")
        cfg.add_to_history("same")
        assert cfg.prompt_history.count("same") == 1

    def test_history_moves_to_top(self):
        cfg = AppConfig()
        cfg.add_to_history("first")
        cfg.add_to_history("second")
        cfg.add_to_history("first")
        assert cfg.prompt_history == ["second", "first"]

    def test_history_max_size(self):
        cfg = AppConfig(max_history_items=5)
        for i in range(10):
            cfg.add_to_history(f"prompt {i}")
        assert len(cfg.prompt_history) == 5
        assert cfg.prompt_history[-1] == "prompt 9"