"""Tests for the provider registry (no network calls)."""

from __future__ import annotations

import pytest

from gpt4free.providers import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    ModelInfo,
    ProviderInfo,
    ProviderStatus,
    PROVIDER_ORDER,
    WORKING_PROVIDERS,
    get_provider_info,
    list_providers,
)


def test_list_providers_non_empty() -> None:
    providers = list_providers()
    assert len(providers) > 0


def test_every_provider_has_at_least_one_model() -> None:
    for p in list_providers():
        assert len(p.model_list) > 0, f"{p.name} has no models"