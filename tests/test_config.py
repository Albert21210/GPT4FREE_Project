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

    def test_save_and_load(self, temp_config_dir):
        mgr = ConfigManager()
        cfg = AppConfig(provider="PollinationsAI", model="openai")
        cfg.add_to_history("test prompt")

        mgr.save(cfg)
        loaded = mgr.load()

        assert loaded.provider == "PollinationsAI"
        assert loaded.model == "openai"
        assert "test prompt" in loaded.prompt_history

    def test_corrupted_config_recovery(self, temp_config_dir):
        mgr = ConfigManager()
        config_path = mgr._config_path

        config_path.write_text("{ this is not json }", encoding="utf-8")

        cfg = mgr.load()
        assert cfg.provider == DEFAULT_PROVIDER
        assert cfg.model == DEFAULT_MODEL

    def test_backup_created_on_save(self, temp_config_dir):
        mgr = ConfigManager()
        cfg = AppConfig()

        mgr.save(cfg)
        backups = list(mgr._backup_path.glob("config_*.json"))
        assert len(backups) == 0

        mgr.save(cfg)
        backups = list(mgr._backup_path.glob("config_*.json"))
        assert len(backups) >= 1

    def test_backup_limit(self, temp_config_dir):
        mgr = ConfigManager()
        cfg = AppConfig()

        for i in range(15):
            cfg.provider = f"Provider{i}"
            mgr.save(cfg)

        backups = list(mgr._backup_path.glob("config_*.json"))
        assert len(backups) <= 10

    def test_export_import(self, temp_config_dir):
        mgr = ConfigManager()
        cfg = AppConfig(provider="PollinationsAI", model="openai")
        mgr.save(cfg)

        export_path = temp_config_dir / "exported.json"
        mgr.export(export_path)

        new_cfg = AppConfig(provider="ChatGptEs", model="gpt-4o")
        mgr.save(new_cfg)
        mgr.import_config(export_path)

        loaded = mgr.load()
        assert loaded.provider == "PollinationsAI"
        assert loaded.model == "openai"

    def test_reset(self, temp_config_dir):
        mgr = ConfigManager()
        cfg = AppConfig(provider="Custom", model="custom")
        mgr.save(cfg)

        mgr.reset()
        loaded = mgr.load()
        assert loaded.provider == DEFAULT_PROVIDER
        assert loaded.model == DEFAULT_MODEL

    def test_rollback(self, temp_config_dir):
        mgr = ConfigManager()

        cfg1 = AppConfig(provider="Provider1", model="model1")
        mgr.save(cfg1)
        mgr.save(cfg1)

        backups = mgr.list_backups()
        assert len(backups) >= 1
        backup_name = backups[0].name

        cfg2 = AppConfig(provider="Provider2", model="model2")
        mgr.save(cfg2)

        mgr.rollback(backup_name)
        loaded = mgr.load()
        assert loaded.provider == "Provider1"


class TestBackwardCompatibility:

    def test_load_config_compat(self, tmp_path):
        with patch("gpt4free.config.user_config_dir", return_value=str(tmp_path)):
            cfg = AppConfig(provider="PollinationsAI", model="openai")
            save_config(cfg)

            loaded = load_config()
            assert loaded.provider == "PollinationsAI"
            assert loaded.model == "openai"

    def test_load_missing_file_compat(self, tmp_path):
        with patch("gpt4free.config.user_config_dir", return_value=str(tmp_path)):
            cfg = load_config()
        assert cfg.provider == DEFAULT_PROVIDER

    def test_load_corrupt_file_compat(self, tmp_path):
        config_path = tmp_path / "gpt4free-tui" / "config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("{ this is not json }", encoding="utf-8")

        with patch("gpt4free.config.user_config_dir", return_value=str(tmp_path)):
            cfg = load_config()
        assert cfg.provider == DEFAULT_PROVIDER


class TestPerformance:

    def test_history_performance(self):
        import time
        cfg = AppConfig(max_history_items=1000)

        start = time.perf_counter()
        for i in range(10000):
            cfg.add_to_history(f"prompt {i}")
        duration = time.perf_counter() - start

        assert duration < 1.0
        assert len(cfg.prompt_history) == 1000

    def test_config_save_performance(self, tmp_path):
        with patch("gpt4free.config.user_config_dir", return_value=str(tmp_path)):
            mgr = ConfigManager()
            cfg = AppConfig()
            for i in range(5000):
                cfg.add_to_history(f"prompt {i}")

            import time
            start = time.perf_counter()
            mgr.save(cfg)
            duration = time.perf_counter() - start

            assert duration < 0.5


class TestProxy:

    def test_default_proxy_is_none(self):
        cfg = AppConfig()
        assert cfg.proxy is None
        assert cfg.force_proxy is False

    def test_set_proxy_basic(self):
        cfg = AppConfig()
        cfg.set_proxy("socks5://127.0.0.1:1080")
        assert cfg.proxy == "socks5://127.0.0.1:1080"
        assert cfg.force_proxy is False

    def test_set_proxy_with_force(self):
        cfg = AppConfig()
        cfg.set_proxy("http://user:pass@host:8080", force=True)
        assert cfg.proxy == "http://user:pass@host:8080"
        assert cfg.force_proxy is True

    def test_set_proxy_strips_whitespace(self):
        cfg = AppConfig()
        cfg.set_proxy("  socks5://127.0.0.1:1080  ")
        assert cfg.proxy == "socks5://127.0.0.1:1080"

    def test_set_proxy_empty_string_clears(self):
        cfg = AppConfig()
        cfg.set_proxy("socks5://127.0.0.1:1080")
        cfg.set_proxy("")
        assert cfg.proxy is None

    def test_clear_proxy(self):
        cfg = AppConfig()
        cfg.set_proxy("socks5://127.0.0.1:1080", force=True)
        cfg.clear_proxy()
        assert cfg.proxy is None
        assert cfg.force_proxy is False

    def test_proxy_roundtrip_through_save_load(self, tmp_path):
        with patch("gpt4free.config.user_config_dir", return_value=str(tmp_path)):
            mgr = ConfigManager()
            cfg = AppConfig()
            cfg.set_proxy("socks5://10.0.0.1:1080", force=True)
            mgr.save(cfg)

            reloaded = mgr.load()
            assert reloaded.proxy == "socks5://10.0.0.1:1080"
            assert reloaded.force_proxy is True

    def test_old_config_without_proxy_field_migrates_cleanly(self):
        old_data = {
            "version": "2.0.0",
            "provider": "PollinationsAI",
            "model": "openai",
        }
        cfg = AppConfig.from_dict(old_data)
        assert cfg.proxy is None
        assert cfg.force_proxy is False

    def test_v1_config_migration_includes_proxy_defaults(self):
        v1_data = {"provider": "PollinationsAI", "model": "openai"}
        cfg = AppConfig.from_dict(v1_data)
        assert cfg.proxy is None
        assert cfg.force_proxy is False

class TestApiKeysAndCustomProviders:

    def test_default_api_keys_empty(self):
        cfg = AppConfig()
        assert cfg.api_keys == {}
        assert cfg.get_api_key("Cerebras") is None

    def test_set_and_get_api_key(self):
        cfg = AppConfig()
        cfg.set_api_key("Cerebras", "sk-test123")
        assert cfg.get_api_key("Cerebras") == "sk-test123"

    def test_set_api_key_empty_string_removes(self):
        cfg = AppConfig()
        cfg.set_api_key("Cerebras", "sk-test123")
        cfg.set_api_key("Cerebras", "")
        assert cfg.get_api_key("Cerebras") is None

    def test_api_key_roundtrip_through_save_load(self, tmp_path):
        with patch("gpt4free.config.user_config_dir", return_value=str(tmp_path)):
            mgr = ConfigManager()
            cfg = AppConfig()
            cfg.set_api_key("Gemini", "sk-abc")
            mgr.save(cfg)

            reloaded = mgr.load()
            assert reloaded.get_api_key("Gemini") == "sk-abc"

    def test_default_custom_providers_empty(self):
        cfg = AppConfig()
        assert cfg.custom_providers == {}

    def test_add_custom_provider(self):
        cfg = AppConfig()
        cfg.add_custom_provider(
            "MyServer",
            "http://localhost:8000/v1",
            [{"alias": "llama3", "display": "Llama 3"}],
            api_key="sk-local",
        )
        assert "MyServer" in cfg.custom_providers
        entry = cfg.custom_providers["MyServer"]
        assert entry["base_url"] == "http://localhost:8000/v1"
        assert entry["api_key"] == "sk-local"
        assert entry["models"] == [{"alias": "llama3", "display": "Llama 3"}]

    def test_remove_custom_provider(self):
        cfg = AppConfig()
        cfg.add_custom_provider("MyServer", "http://localhost:8000/v1", [{"alias": "llama3", "display": "Llama 3"}])
        cfg.remove_custom_provider("MyServer")
        assert "MyServer" not in cfg.custom_providers

    def test_remove_nonexistent_custom_provider_is_noop(self):
        cfg = AppConfig()
        cfg.remove_custom_provider("DoesNotExist") 
        assert cfg.custom_providers == {}

    def test_custom_provider_roundtrip_through_save_load(self, tmp_path):
        with patch("gpt4free.config.user_config_dir", return_value=str(tmp_path)):
            mgr = ConfigManager()
            cfg = AppConfig()
            cfg.add_custom_provider(
                "Together",
                "https://api.together.xyz/v1",
                [{"alias": "meta-llama/Llama-3-70b", "display": "Llama 3 70B"}],
                api_key="sk-together",
            )
            mgr.save(cfg)

            reloaded = mgr.load()
            assert "Together" in reloaded.custom_providers
            assert reloaded.custom_providers["Together"]["api_key"] == "sk-together"

    def test_old_config_without_new_fields_migrates_cleanly(self):
        """Configs saved before api_keys/custom_providers existed shouldn't crash."""
        old_data = {
            "version": "2.0.0",
            "provider": "PollinationsAI",
            "model": "openai",
        }
        cfg = AppConfig.from_dict(old_data)
        assert cfg.api_keys == {}
        assert cfg.custom_providers == {}

    def test_v1_config_migration_includes_new_field_defaults(self):
        v1_data = {"provider": "PollinationsAI", "model": "openai"}
        cfg = AppConfig.from_dict(v1_data)
        assert cfg.api_keys == {}
        assert cfg.custom_providers == {}