from __future__ import annotations
from unittest.mock import patch
from gpt4free.config import AppConfig, ConfigManager


class TestBuiltinToolsToggle:

    def test_builtin_tools_enabled_by_default(self):
        cfg = AppConfig()
        assert cfg.builtin_tools_enabled is True

    def test_old_config_without_field_migrates_to_enabled(self):
        old_data = {"version": "2.0.0", "provider": "PollinationsAI", "model": "openai"}
        cfg = AppConfig.from_dict(old_data)
        assert cfg.builtin_tools_enabled is True

    def test_v1_config_migration_includes_default(self):
        v1_data = {"provider": "PollinationsAI", "model": "openai"}
        cfg = AppConfig.from_dict(v1_data)
        assert cfg.builtin_tools_enabled is True


class TestMcpServers:

    def test_no_servers_by_default(self):
        cfg = AppConfig()
        assert cfg.mcp_servers == {}

    def test_add_mcp_server_basic(self):
        cfg = AppConfig()
        cfg.add_mcp_server("dummy", command="python", args=["server.py"])
        assert "dummy" in cfg.mcp_servers
        entry = cfg.mcp_servers["dummy"]
        assert entry["command"] == "python"
        assert entry["args"] == ["server.py"]
        assert entry["enabled"] is True

    def test_add_mcp_server_defaults_args_and_env(self):
        cfg = AppConfig()
        cfg.add_mcp_server("simple", command="npx")
        assert cfg.mcp_servers["simple"]["args"] == []
        assert cfg.mcp_servers["simple"]["env"] == {}

    def test_add_mcp_server_disabled(self):
        cfg = AppConfig()
        cfg.add_mcp_server("dummy", command="python", enabled=False)
        assert cfg.mcp_servers["dummy"]["enabled"] is False

    def test_remove_mcp_server(self):
        cfg = AppConfig()
        cfg.add_mcp_server("dummy", command="python")
        cfg.remove_mcp_server("dummy")
        assert "dummy" not in cfg.mcp_servers

    def test_remove_unknown_mcp_server_is_noop(self):
        cfg = AppConfig()
        cfg.remove_mcp_server("nope")  # should not raise
        assert cfg.mcp_servers == {}

    def test_set_mcp_server_enabled(self):
        cfg = AppConfig()
        cfg.add_mcp_server("dummy", command="python")
        cfg.set_mcp_server_enabled("dummy", False)
        assert cfg.mcp_servers["dummy"]["enabled"] is False
        cfg.set_mcp_server_enabled("dummy", True)
        assert cfg.mcp_servers["dummy"]["enabled"] is True

    def test_set_enabled_unknown_server_is_noop(self):
        cfg = AppConfig()
        cfg.set_mcp_server_enabled("nope", False)  # should not raise
        assert cfg.mcp_servers == {}

    def test_mcp_servers_roundtrip_through_save_load(self, tmp_path):
        with patch("gpt4free.config.config_manager.user_config_dir", return_value=str(tmp_path)):
            mgr = ConfigManager()
            cfg = AppConfig()
            cfg.add_mcp_server("dummy", command="python", args=["s.py"], env={"KEY": "val"})
            mgr.save(cfg)

            reloaded = mgr.load()
            assert reloaded.mcp_servers["dummy"]["command"] == "python"
            assert reloaded.mcp_servers["dummy"]["args"] == ["s.py"]
            assert reloaded.mcp_servers["dummy"]["env"] == {"KEY": "val"}

    def test_old_config_without_mcp_servers_migrates_cleanly(self):
        old_data = {"version": "2.0.0", "provider": "PollinationsAI", "model": "openai"}
        cfg = AppConfig.from_dict(old_data)
        assert cfg.mcp_servers == {}
