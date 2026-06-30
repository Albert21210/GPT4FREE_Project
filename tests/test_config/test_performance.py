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

        assert duration < 1.0
        assert len(cfg.prompt_history) == 1000

    def test_config_save_performance(self, tmp_path):
        with patch("gpt4free.config.config_manager.user_config_dir", return_value=str(tmp_path)):
            mgr = ConfigManager()
            cfg = AppConfig()
            for i in range(5000):
                cfg.add_to_history(f"prompt {i}")

            start = time.perf_counter()
            mgr.save(cfg)
            duration = time.perf_counter() - start

            assert duration < 0.5