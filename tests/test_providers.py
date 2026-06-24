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


def test_default_provider_in_list() -> None:
    info = get_provider_info(DEFAULT_PROVIDER)
    assert info is not None, f"{DEFAULT_PROVIDER} not found in provider list"


def test_default_model_in_default_provider() -> None:
    info = get_provider_info(DEFAULT_PROVIDER)
    assert info is not None
    aliases = [m.alias for m in info.model_list]
    assert DEFAULT_MODEL in aliases, (
        f"{DEFAULT_MODEL} not found in {DEFAULT_PROVIDER} model list: {aliases}"
    )


def test_provider_info_types() -> None:
    p = list_providers()[0]
    assert isinstance(p, ProviderInfo)
    m = p.model_list[0]
    assert isinstance(m, ModelInfo)
    assert isinstance(m.alias, str) and m.alias
    assert isinstance(m.display, str) and m.display