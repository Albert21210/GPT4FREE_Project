"""Manual smoke-check script: hits real provider APIs over the network to see
which (provider, model) pairs currently respond. NOT a pytest test (functions
are prefixed `check_*`, not `test_*`, on purpose — pytest would otherwise try
to collect `check_model(provider_name, model)` as a test needing fixtures).

Run directly:
    python tests/test_all_models.py
"""

import asyncio

import g4f

from gpt4free.providers import WORKING_PROVIDERS

# Use the live, maintained registry from gpt4free.providers instead of a
# hardcoded (and quickly stale) duplicate list.
PROVIDERS_MODELS = {name: [alias for alias, _ in models] for name, models in WORKING_PROVIDERS.items()}


async def check_model(provider_name: str, model: str) -> tuple[bool, str]:
    try:
        provider = getattr(g4f.Provider, provider_name, None)
        if not provider:
            return False, "Provider not found"

        print(f"Testing {provider_name}/{model}...")
        response = await asyncio.to_thread(
            g4f.ChatCompletion.create,
            model=model,
            messages=[{"role": "user", "content": "Say just one word: ok"}],
            provider=provider,
            stream=False,
            timeout=30,
        )
        if response and len(str(response)) > 0:
            print(f"✅ {provider_name}/{model} WORKS!")
            return True, str(response)[:50]
        return False, "Empty response"
    except Exception as e:
        error_msg = str(e)[:80]
        print(f"❌ {provider_name}/{model} FAILED: {error_msg}")
        return False, error_msg


async def main() -> None:
    print("🔍 TESTING ALL PROVIDERS AND MODELS...\n")
    working: dict[str, list[str]] = {}

    for provider, models in PROVIDERS_MODELS.items():
        working[provider] = []
        for model in models:
            success, _msg = await check_model(provider, model)
            if success:
                working[provider].append(model)
            await asyncio.sleep(1)  # rate-limit friendly delay

    print("\n" + "=" * 60)
    print("📊 WORKING MODELS BY PROVIDER:")
    print("=" * 60)
    for provider, models in working.items():
        if models:
            print(f"\n✅ {provider}:")
            for model in models:
                print(f"   - {model}")
        else:
            print(f"\n❌ {provider}: No working models")


if __name__ == "__main__":
    asyncio.run(main())
