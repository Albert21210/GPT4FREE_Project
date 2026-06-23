"""Async chat session — uses g4f.client.AsyncClient (modern API)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Optional

from gpt4free.providers import get_provider_class
