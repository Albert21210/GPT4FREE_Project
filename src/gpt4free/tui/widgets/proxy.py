"""Modal screen for configuring an optional outbound proxy.

A proxy is only needed for providers that are geoblocked at the company
level (Gemini, MetaAI, Grok — see gpt4free.providers.PROXY_REQUIRED_PROVIDERS).
By default it stays OFF and is only applied to those providers; users can
opt in to routing every provider through it via the "force" checkbox.
"""
