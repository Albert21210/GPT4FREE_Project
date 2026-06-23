from __future__ import annotations
import json
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Self
from platformdirs import user_config_dir
from gpt4free.providers import DEFAULT_MODEL, DEFAULT_PROVIDER

APP_NAME: str = "gpt4free-tui"
CONFIG_VERSION: str = "2.0.0"