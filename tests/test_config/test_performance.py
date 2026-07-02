from __future__ import annotations
import time
from unittest.mock import patch
from gpt4free.config import AppConfig, ConfigManager


class TestPerformance:

    def test_history_performance(self):
        cfg = AppConfig(max_history_items=1000)

        start = time.perf_counter()
        for i in range(10000):
            cfg.add_to_history(f"prompt {i}")
        duration = time.perf_counter() - start

        assert duration < 2.0
        assert len(cfg.prompt_history) == 1000

    def test_config_save_performance(self, tmp_path):
        config_dir = tmp_path / "gpt4free-tui"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with patch("gpt4free.config.config_manager.user_config_dir", return_value=str(tmp_path)):
            mgr = ConfigManager()
            mgr._config_path = config_dir / "config.json"
            mgr._backup_path = config_dir / "backups"
            mgr._backup_path.mkdir(exist_ok=True)
            
            cfg = AppConfig()
            for i in range(5000):
                cfg.add_to_history(f"prompt {i}")

            start = time.perf_counter()
            mgr.save(cfg)
            duration = time.perf_counter() - start

            assert duration < 1.0
