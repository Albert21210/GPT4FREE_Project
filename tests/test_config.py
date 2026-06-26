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