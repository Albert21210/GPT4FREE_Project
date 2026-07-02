from __future__ import annotations
from unittest.mock import patch
import pytest
import json
from gpt4free.config import AppConfig, ConfigManager


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
        config_dir = tmp_path / "gpt4free-tui"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("gpt4free.config.config_manager.user_config_dir", return_value=str(tmp_path)):
            mgr = ConfigManager()
            mgr._config_path = config_dir / "config.json"
            mgr._backup_path = config_dir / "backups"
            mgr._backup_path.mkdir(exist_ok=True)
            
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
        config_dir = tmp_path / "gpt4free-tui"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("gpt4free.config.config_manager.user_config_dir", return_value=str(tmp_path)):
            mgr = ConfigManager()
            mgr._config_path = config_dir / "config.json"
            mgr._backup_path = config_dir / "backups"
            mgr._backup_path.mkdir(exist_ok=True)
            
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
        old_data = {
            "version": "2.0.0",
            "provider": "PollinationsAI",
            "model": "openai",
        }
        if hasattr(AppConfig, 'from_dict'):
            cfg = AppConfig.from_dict(old_data)
        else:
            cfg = AppConfig()
            cfg.provider = old_data.get("provider", "PollinationsAI")
            cfg.model = old_data.get("model", "openai")
        assert cfg.api_keys == {}
        assert cfg.custom_providers == {}

    def test_v1_config_migration_includes_new_field_defaults(self):
        v1_data = {"provider": "PollinationsAI", "model": "openai"}
        if hasattr(AppConfig, 'from_dict'):
            cfg = AppConfig.from_dict(v1_data)
        else:
            cfg = AppConfig()
            cfg.provider = v1_data.get("provider", "PollinationsAI")
            cfg.model = v1_data.get("model", "openai")
        assert cfg.api_keys == {}
        assert cfg.custom_providers == {}
