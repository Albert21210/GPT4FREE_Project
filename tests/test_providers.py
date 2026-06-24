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


def test_default_status_is_working() -> None:
    """All curated providers start as WORKING before probing."""
    for p in list_providers():
        assert p.status == ProviderStatus.WORKING


def test_provider_order_respected() -> None:
    """Providers in PROVIDER_ORDER come first in list_providers()."""
    names = [p.name for p in list_providers()]
    ordered_present = [n for n in PROVIDER_ORDER if n in WORKING_PROVIDERS]
    assert names[: len(ordered_present)] == ordered_present


def test_no_duplicate_providers() -> None:
    names = [p.name for p in list_providers()]
    assert len(names) == len(set(names)), "Duplicate providers in list"


def test_no_empty_aliases() -> None:
    for p in list_providers():
        for m in p.model_list:
            assert m.alias.strip(), f"Empty alias in {p.name}"
            assert m.display.strip(), f"Empty display in {p.name}"


def test_status_label_format() -> None:
    p = list_providers()[0]
    label = p.status_label
    assert "working" in label


def test_models_property() -> None:
    p = list_providers()[0]
    assert p.models == [m.alias for m in p.model_list]


def test_working_providers_dict_integrity() -> None:
    """All entries in WORKING_PROVIDERS are valid (alias, display) tuples."""
    for name, entries in WORKING_PROVIDERS.items():
        assert isinstance(name, str) and name
        for alias, display in entries:
            assert isinstance(alias, str) and alias, f"Bad alias in {name}"
            assert isinstance(display, str) and display, f"Bad display in {name}"
