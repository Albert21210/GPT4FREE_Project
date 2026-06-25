import asyncio
import g4f

PROVIDERS_MODELS = {
    "PollinationsAI": ["openai", "openai-large", "deepseek-r1", "deepseek-v3", "mistral", "llama", "qwen-coder-large", "qwen-large", "phi"],
    "BlackboxPro": ["gpt-4o", "gpt-4o-mini", "deepseek-r1", "deepseek-v3", "gemini-2.0-flash", "llama-3.3-70b", "mistral-large"],
    "ChatGptEs": ["gpt-4o", "gpt-4o-mini"],
    "Nexra": ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
    "DeepInfraChat": ["meta-llama/Meta-Llama-3.1-70B-Instruct", "meta-llama/Meta-Llama-3.1-8B-Instruct", "mistralai/Mistral-7B-Instruct-v0.3"],
    "DuckDuckGo": ["gpt-4o-mini", "claude-3-haiku", "llama-3.3-70b", "mixtral-8x7b"],
}


async def test_model(provider_name, model):
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