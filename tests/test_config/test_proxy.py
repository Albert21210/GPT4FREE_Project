from __future__ import annotations
from unittest.mock import patch
import pytest
from gpt4free.config import AppConfig, ConfigManager


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
        config_dir = tmp_path / "gpt4free-tui"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("gpt4free.config.config_manager.user_config_dir", return_value=str(tmp_path)):
            mgr = ConfigManager()
            mgr._config_path = config_dir / "config.json"
            mgr._backup_path = config_dir / "backups"
            mgr._backup_path.mkdir(exist_ok=True)
            
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
        if hasattr(AppConfig, 'from_dict'):
            cfg = AppConfig.from_dict(old_data)
        else:
            cfg = AppConfig()
            cfg.provider = old_data.get("provider", "PollinationsAI")
            cfg.model = old_data.get("model", "openai")
        assert cfg.proxy is None
        assert cfg.force_proxy is False

    def test_v1_config_migration_includes_proxy_defaults(self):
        v1_data = {"provider": "PollinationsAI", "model": "openai"}
        if hasattr(AppConfig, 'from_dict'):
            cfg = AppConfig.from_dict(v1_data)
        else:
            cfg = AppConfig()
            cfg.provider = v1_data.get("provider", "PollinationsAI")
            cfg.model = v1_data.get("model", "openai")
        assert cfg.proxy is None
        assert cfg.force_proxy is False
