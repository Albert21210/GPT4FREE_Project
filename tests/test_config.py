from __future__ import annotations
from unittest.mock import patch
import pytest
from gpt4free.config import AppConfig, ConfigManager, load_config, save_config
from gpt4free.providers import DEFAULT_MODEL, DEFAULT_PROVIDER


class TestAppConfig: