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

    def test_stats_update(self):
        cfg = AppConfig()
        assert cfg.stats["total_queries"] == 0
        cfg.add_to_history("test")
        assert cfg.stats["total_queries"] == 1
        assert "last_used" in cfg.stats
        assert "first_used" in cfg.stats

    def test_get_recent_history(self):
        cfg = AppConfig()
        for i in range(10):
            cfg.add_to_history(f"prompt {i}")
        recent = cfg.get_recent_history(3)
        assert recent == ["prompt 7", "prompt 8", "prompt 9"]

    def test_search_history(self):
        cfg = AppConfig()
        prompts = ["hello world", "test hello", "goodbye"]
        for p in prompts:
            cfg.add_to_history(p)
        results = cfg.search_history("hello")
        assert results == ["test hello", "hello world"]

    def test_clear_history(self):
        cfg = AppConfig()
        cfg.add_to_history("test")
        cfg.clear_history()
        assert cfg.prompt_history == []

    def test_profile_management(self):
        cfg = AppConfig(provider="PollinationsAI", model="openai")
        cfg.save_profile("work")
        cfg.save_profile("personal")

        cfg.provider = "ChatGptEs"
        cfg.model = "gpt-4o"

        cfg.load_profile("work")
        assert cfg.provider == "PollinationsAI"
        assert cfg.model == "openai"
        assert cfg.active_profile == "work"

    def test_to_dict_roundtrip(self):
        cfg = AppConfig(provider="PollinationsAI", model="openai")
        cfg.add_to_history("test")
        d = cfg.to_dict()

        assert d["version"] == "2.0.0"
        assert "_meta" in d
        assert "config_hash" in d["_meta"]

        restored = AppConfig.from_dict(d)
        assert restored.provider == cfg.provider
        assert restored.model == cfg.model
        assert restored.prompt_history == cfg.prompt_history

    def test_from_dict_ignores_unknown_keys(self):
        d = {
            "provider": "PollinationsAI",
            "model": "openai",
            "unknown_future_key": 99,
            "another_unknown": "value"
        }
        cfg = AppConfig.from_dict(d)
        assert cfg.provider == "PollinationsAI"
        assert cfg.model == "openai"
        assert not hasattr(cfg, "unknown_future_key")

    def test_migration_from_v1(self):
        v1_data = {
            "provider": "PollinationsAI",
            "model": "openai",
            "stream": True,
            "syntax_theme": "monokai",
            "max_history_items": 200,
            "prompt_history": ["old", "history"]
        }
        cfg = AppConfig.from_dict(v1_data)
        assert cfg.version == "2.0.0"
        assert cfg.stats == {"total_queries": 0, "first_used": None, "last_used": None}

    def test_invalid_config_raises_error(self):
        invalid_data = {"provider": "PollinationsAI"}
        with pytest.raises(ValueError):
            AppConfig.from_dict(invalid_data)


class TestConfigManager:

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        with patch("gpt4free.config.user_config_dir", return_value=str(tmp_path)):
            yield tmp_path