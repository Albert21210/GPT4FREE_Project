from __future__ import annotations
from unittest.mock import patch
import pytest
import json
from gpt4free.config import AppConfig, ConfigManager
from gpt4free.providers import DEFAULT_MODEL, DEFAULT_PROVIDER


class TestConfigManager:

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        config_dir = tmp_path / "gpt4free-tui"
        config_dir.mkdir(parents=True, exist_ok=True)
        with patch("gpt4free.config.config_manager.user_config_dir", return_value=str(tmp_path)):
            yield config_dir

    def test_save_and_load(self, temp_config_dir):
        mgr = ConfigManager()
        mgr._config_path = temp_config_dir / "config.json"
        mgr._backup_path = temp_config_dir / "backups"
        mgr._backup_path.mkdir(exist_ok=True)
        
        cfg = AppConfig(provider="PollinationsAI", model="openai")
        cfg.add_to_history("test prompt")

        mgr.save(cfg)
        loaded = mgr.load()

        assert loaded.provider == "PollinationsAI"
        assert loaded.model == "openai"
        assert "test prompt" in loaded.prompt_history

    def test_corrupted_config_recovery(self, temp_config_dir):
        mgr = ConfigManager()
        mgr._config_path = temp_config_dir / "config.json"
        mgr._backup_path = temp_config_dir / "backups"
        mgr._backup_path.mkdir(exist_ok=True)
        
        config_path = mgr._config_path
        config_path.write_text("{ this is not json }", encoding="utf-8")

        cfg = mgr.load()
        assert cfg.provider == DEFAULT_PROVIDER
        assert cfg.model == DEFAULT_MODEL

    def test_backup_created_on_save(self, temp_config_dir):
        mgr = ConfigManager()
        mgr._config_path = temp_config_dir / "config.json"
        mgr._backup_path = temp_config_dir / "backups"
        mgr._backup_path.mkdir(exist_ok=True)
        
        cfg = AppConfig()

        mgr.save(cfg)
        backups = list(mgr._backup_path.glob("config_*.json"))
        assert len(backups) >= 0

        mgr.save(cfg)
        backups = list(mgr._backup_path.glob("config_*.json"))
        assert len(backups) >= 1

    def test_backup_limit(self, temp_config_dir):
        mgr = ConfigManager()
        mgr._config_path = temp_config_dir / "config.json"
        mgr._backup_path = temp_config_dir / "backups"
        mgr._backup_path.mkdir(exist_ok=True)
        
        cfg = AppConfig()

        for i in range(15):
            cfg.provider = f"Provider{i}"
            mgr.save(cfg)

        backups = list(mgr._backup_path.glob("config_*.json"))
        assert len(backups) <= 10

    def test_export_import(self, temp_config_dir):
        mgr = ConfigManager()
        mgr._config_path = temp_config_dir / "config.json"
        mgr._backup_path = temp_config_dir / "backups"
        mgr._backup_path.mkdir(exist_ok=True)
        
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
        mgr._config_path = temp_config_dir / "config.json"
        mgr._backup_path = temp_config_dir / "backups"
        mgr._backup_path.mkdir(exist_ok=True)
        
        cfg = AppConfig(provider="Custom", model="custom")
        mgr.save(cfg)

        mgr.reset()
        loaded = mgr.load()
        assert loaded.provider == DEFAULT_PROVIDER
        assert loaded.model == DEFAULT_MODEL

    def test_rollback(self, temp_config_dir):
        mgr = ConfigManager()
        mgr._config_path = temp_config_dir / "config.json"
        mgr._backup_path = temp_config_dir / "backups"
        mgr._backup_path.mkdir(exist_ok=True)

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
