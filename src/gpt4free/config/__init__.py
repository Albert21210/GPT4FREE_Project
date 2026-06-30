from gpt4free.config.app_config import AppConfig
from gpt4free.config.config_manager import ConfigManager
from gpt4free.config.config_schema import APP_NAME, CONFIG_VERSION, CONFIG_SCHEMA


def load_config() -> AppConfig:
    return ConfigManager().load()

def save_config(cfg: AppConfig) -> None:
    ConfigManager().save(cfg)

__all__ = [
    "AppConfig",
    "ConfigManager",
    "APP_NAME",
    "CONFIG_VERSION",
    "CONFIG_SCHEMA",
    "load_config",
    "save_config",
]