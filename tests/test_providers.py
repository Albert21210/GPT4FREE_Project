"""Tests for the provider registry (no network calls)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gpt4free.providers import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    ModelInfo,
    ProviderInfo,
    ProviderStatus,
    PROVIDER_ORDER,
    WORKING_PROVIDERS,
    custom_providers_to_info,
    get_provider_class,
    get_provider_info,
    list_providers,
    probe_all,
    probe_provider,
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


# custom providers

def test_custom_providers_to_info_empty() -> None:
    assert custom_providers_to_info(None) == []
    assert custom_providers_to_info({}) == []


def test_custom_providers_to_info_basic() -> None:
    custom = {
        "MyServer": {
            "base_url": "http://localhost:8080/v1",
            "api_key": "sk-local",
            "models": [{"alias": "local-7b", "display": "Local 7B"}],
        }
    }
    infos = custom_providers_to_info(custom)
    assert len(infos) == 1
    info = infos[0]
    assert info.name == "MyServer"
    assert info.is_custom is True
    assert info.base_url == "http://localhost:8080/v1"
    assert info.needs_auth is True  # has an api_key configured
    assert info.needs_proxy is False
    assert info.model_list[0].alias == "local-7b"


def test_custom_providers_to_info_no_api_key_needs_auth_false() -> None:
    custom = {
        "OpenServer": {
            "base_url": "http://localhost:9000/v1",
            "api_key": "",
            "models": [{"alias": "m1", "display": "M1"}],
        }
    }
    infos = custom_providers_to_info(custom)
    assert infos[0].needs_auth is False


def test_list_providers_includes_custom() -> None:
    custom = {
        "MyServer": {
            "base_url": "http://localhost:8080/v1",
            "api_key": "",
            "models": [{"alias": "local-7b", "display": "Local 7B"}],
        }
    }
    names = [p.name for p in list_providers(custom)]
    assert "MyServer" in names
    # Built-ins still present and still ordered first
    assert names[0] == PROVIDER_ORDER[0]


def test_list_providers_without_custom_unaffected() -> None:
    """Passing no custom_providers should behave exactly as before."""
    names_default = [p.name for p in list_providers()]
    names_explicit_none = [p.name for p in list_providers(None)]
    assert names_default == names_explicit_none


def test_get_provider_info_finds_custom() -> None:
    custom = {
        "MyServer": {
            "base_url": "http://localhost:8080/v1",
            "api_key": "",
            "models": [{"alias": "local-7b", "display": "Local 7B"}],
        }
    }
    info = get_provider_info("MyServer", custom)
    assert info is not None
    assert info.is_custom is True


# probe_provider / probe_all with api_key & custom provider

@pytest.mark.asyncio
async def test_probe_provider_custom_routes_to_http_probe() -> None:
    info = ProviderInfo(
        name="MyServer",
        model_list=[ModelInfo(alias="m1", display="M1")],
        is_custom=True,
        base_url="http://localhost:8080/v1",
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"choices": [{"message": {"content": "hello"}}]}

    mock_http_client = MagicMock()
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)
    mock_http_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_http_client):
        result = await probe_provider(info)

    assert result.status == ProviderStatus.WORKING
    assert result.detail == "ok"


@pytest.mark.asyncio
async def test_probe_provider_custom_missing_base_url() -> None:
    info = ProviderInfo(
        name="Broken",
        model_list=[ModelInfo(alias="m1", display="M1")],
        is_custom=True,
        base_url=None,
    )
    result = await probe_provider(info)
    assert result.status == ProviderStatus.DOWN
    assert "base_url" in result.detail


@pytest.mark.asyncio
async def test_probe_provider_custom_auth_required_on_401() -> None:
    info = ProviderInfo(
        name="MyServer",
        model_list=[ModelInfo(alias="m1", display="M1")],
        is_custom=True,
        base_url="http://localhost:8080/v1",
    )

    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.text = "unauthorized"

    mock_http_client = MagicMock()
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)
    mock_http_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_http_client):
        result = await probe_provider(info)

    assert result.status == ProviderStatus.AUTH_REQUIRED
    assert "401" in result.detail


@pytest.mark.asyncio
async def test_probe_provider_passes_api_key_to_builtin() -> None:
    info = ProviderInfo(name="Cerebras", model_list=[ModelInfo(alias="llama-3.3-70b", display="Llama")])

    mock_message = MagicMock()
    mock_message.content = "hello"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("g4f.client.AsyncClient", return_value=mock_client), \
         patch("gpt4free.providers.get_provider_class", return_value=MagicMock()):
        result = await probe_provider(info, api_key="sk-test-789")

    assert result.status == ProviderStatus.WORKING
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs.get("api_key") == "sk-test-789"


@pytest.mark.asyncio
async def test_probe_all_forwards_api_keys_dict() -> None:
    info = ProviderInfo(
        name="Cerebras",
        model_list=[ModelInfo(alias="llama-3.3-70b", display="Llama")],
        needs_proxy=False,
    )

    mock_message = MagicMock()
    mock_message.content = "hello"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("g4f.client.AsyncClient", return_value=mock_client), \
         patch("gpt4free.providers.get_provider_class", return_value=MagicMock()):
        results = await probe_all([info], api_keys={"Cerebras": "sk-abc"})

    assert results[0].status == ProviderStatus.WORKING
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs.get("api_key") == "sk-abc"


# get_provider_class: g4f lazy-loader race-condition workaround

def test_get_provider_class_returns_class_directly() -> None:
    """The normal, non-racy path: g4f.Provider attribute is already a class."""
    fake_cls = type("FakeProvider", (), {})

    with patch("g4f.Provider") as mock_provider_pkg:
        mock_provider_pkg.FakeProvider = fake_cls
        result = get_provider_class("FakeProvider")
    assert result is fake_cls


def test_get_provider_class_recovers_from_module_race() -> None:
    """If g4f's lazy-loader hands back the raw submodule (race condition),
    we should dig the real class out of it instead of returning a module."""
    import types

    fake_cls = type("PollinationsAI", (), {})
    fake_submodule = types.ModuleType("g4f.Provider.PollinationsAI")
    fake_submodule.PollinationsAI = fake_cls

    with patch("g4f.Provider") as mock_provider_pkg:
        mock_provider_pkg.PollinationsAI = fake_submodule
        result = get_provider_class("PollinationsAI")

    assert result is fake_cls
    assert not isinstance(result, types.ModuleType)


def test_get_provider_class_unknown_name_returns_none() -> None:
    with patch("g4f.Provider") as mock_provider_pkg:
        mock_provider_pkg.configure_mock(**{"NotARealProvider": None})
        # getattr with default None simulates an unknown attribute
        del mock_provider_pkg.NotARealProvider
        result = get_provider_class("NotARealProvider")
    assert result is None


# fetch_live_models: live model catalog straight from the provider

@pytest.mark.asyncio
async def test_fetch_live_models_unknown_provider_returns_empty() -> None:
    from gpt4free.providers import fetch_live_models
    with patch("gpt4free.providers.get_provider_class", return_value=None):
        models = await fetch_live_models("DoesNotExist")
    assert models == []


@pytest.mark.asyncio
async def test_fetch_live_models_no_get_models_returns_empty() -> None:
    from gpt4free.providers import fetch_live_models

    class NoGetModels:
        pass

    with patch("gpt4free.providers.get_provider_class", return_value=NoGetModels):
        models = await fetch_live_models("SomeProvider")
    assert models == []


@pytest.mark.asyncio
async def test_fetch_live_models_returns_model_info_list() -> None:
    from gpt4free.providers import fetch_live_models

    class FakeProvider:
        @classmethod
        def get_models(cls, **kwargs):
            return ["gpt-5.4", "gpt-5.4-mini", "openai-large"]

    with patch("gpt4free.providers.get_provider_class", return_value=FakeProvider):
        models = await fetch_live_models("PollinationsAI")

    assert len(models) == 3
    assert all(isinstance(m, ModelInfo) for m in models)
    assert [m.alias for m in models] == ["gpt-5.4", "gpt-5.4-mini", "openai-large"]


@pytest.mark.asyncio
async def test_fetch_live_models_passes_api_key() -> None:
    from gpt4free.providers import fetch_live_models

    captured = {}

    class FakeProvider:
        @classmethod
        def get_models(cls, **kwargs):
            captured.update(kwargs)
            return ["model-a"]

    with patch("gpt4free.providers.get_provider_class", return_value=FakeProvider):
        await fetch_live_models("Cerebras", api_key="sk-test")

    assert captured.get("api_key") == "sk-test"


@pytest.mark.asyncio
async def test_fetch_live_models_handles_exception_gracefully() -> None:
    from gpt4free.providers import fetch_live_models

    class FakeProvider:
        @classmethod
        def get_models(cls, **kwargs):
            raise RuntimeError("network unreachable")

    with patch("gpt4free.providers.get_provider_class", return_value=FakeProvider):
        models = await fetch_live_models("PollinationsAI")
    assert models == []


@pytest.mark.asyncio
async def test_fetch_live_models_handles_timeout_gracefully() -> None:
    import asyncio as _asyncio
    from gpt4free.providers import fetch_live_models

    class FakeProvider:
        @classmethod
        def get_models(cls, **kwargs):
            import time
            time.sleep(0.2)
            return ["slow-model"]

    with patch("gpt4free.providers.get_provider_class", return_value=FakeProvider):
        models = await fetch_live_models("PollinationsAI", timeout=0.01)
    assert models == []


@pytest.mark.asyncio
async def test_fetch_live_models_empty_result_returns_empty_list() -> None:
    from gpt4free.providers import fetch_live_models

    class FakeProvider:
        @classmethod
        def get_models(cls, **kwargs):
            return []

    with patch("gpt4free.providers.get_provider_class", return_value=FakeProvider):
        models = await fetch_live_models("PollinationsAI")
    assert models == []


# requires_browser flag & extended timeout for nodriver-based providers

def test_probe_provider_info_default_requires_browser_false() -> None:
    info = ProviderInfo(name="PollinationsAI", model_list=[ModelInfo(alias="m1", display="M1")])
    assert info.requires_browser is False


@pytest.mark.asyncio
async def test_probe_provider_detects_use_nodriver_and_sets_flag() -> None:
    info = ProviderInfo(name="Pi", model_list=[ModelInfo(alias="pi", display="Pi")])

    class FakeNodriverProvider:
        use_nodriver = True

    mock_message = MagicMock()
    mock_message.content = "hi"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch("g4f.client.AsyncClient", return_value=mock_client), \
         patch("gpt4free.providers.get_provider_class", return_value=FakeNodriverProvider):
        result = await probe_provider(info)

    assert result.requires_browser is True
    assert result.status == ProviderStatus.WORKING


@pytest.mark.asyncio
async def test_probe_provider_uses_longer_timeout_for_browser_providers() -> None:
    from gpt4free.providers import PROBE_TIMEOUT_BROWSER

    info = ProviderInfo(name="Pi", model_list=[ModelInfo(alias="pi", display="Pi")])

    class FakeNodriverProvider:
        use_nodriver = True

    captured_timeout = {}

    async def fake_wait_for(coro, timeout):
        captured_timeout["value"] = timeout
        coro.close()
        raise __import__("asyncio").TimeoutError()

    with patch("g4f.client.AsyncClient"), \
         patch("gpt4free.providers.get_provider_class", return_value=FakeNodriverProvider), \
         patch("asyncio.wait_for", side_effect=fake_wait_for):
        result = await probe_provider(info)

    assert captured_timeout["value"] == PROBE_TIMEOUT_BROWSER
    assert result.status == ProviderStatus.DOWN
    assert "browser window" in result.detail
