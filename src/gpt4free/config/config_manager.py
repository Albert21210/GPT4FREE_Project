from __future__ import annotations
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from platformdirs import user_config_dir

from gpt4free.config.app_config import AppConfig
from gpt4free.config.config_schema import APP_NAME


class ConfigManager:

    def __init__(self, app_name: str = APP_NAME):
        self.app_name = app_name
        self._config_path = self._get_config_path()
        self._backup_path = self._config_path.parent / "config.backups"
        self._backup_path.mkdir(parents=True, exist_ok=True)

    def _get_config_path(self) -> Path:
        path = Path(user_config_dir(self.app_name))
        path.mkdir(parents=True, exist_ok=True)
        return path / "config.json"

    def load(self) -> AppConfig:
        if not self._config_path.exists():
            return AppConfig()

        self._backup_current()

        try:
            raw = self._config_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return AppConfig.from_dict(data)
        except (json.JSONDecodeError, ValueError, TypeError):
            return self._recover_from_backup()

    def save(self, config: AppConfig) -> None:
        self._backup_current()

        temp_path = self._config_path.with_suffix(".tmp")
        try:
            temp_path.write_text(
                json.dumps(config.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            temp_path.replace(self._config_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

    def _backup_current(self) -> None:
        if not self._config_path.exists():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self._backup_path / f"config_{timestamp}.json"
        shutil.copy2(self._config_path, backup_file)

        backups = sorted(self._backup_path.glob("config_*.json"))
        for old_backup in backups[:-10]:
            old_backup.unlink()

    def _recover_from_backup(self) -> AppConfig:
        backups = sorted(self._backup_path.glob("config_*.json"))
        if not backups:
            return AppConfig()

        latest = backups[-1]
        try:
            raw = latest.read_text(encoding="utf-8")
            data = json.loads(raw)
            return AppConfig.from_dict(data)
        except Exception:
            return AppConfig()

    def list_backups(self) -> list[Path]:
        return sorted(self._backup_path.glob("config_*.json"))

    def rollback(self, backup_name: str) -> None:
        backup_path = self._backup_path / backup_name
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup '{backup_name}' not found")

        shutil.copy2(backup_path, self._config_path)

    def export(self, path: Path) -> None:
        config = self.load()
        path.write_text(
            json.dumps(config.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def import_config(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"Config file '{path}' not found")

        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        config = AppConfig.from_dict(data)
        self.save(config)

    def reset(self) -> None:
        if self._config_path.exists():
            self._backup_current()
            self._config_path.unlink()

        config = AppConfig()
        self.save(config)