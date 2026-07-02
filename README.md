# GPT4FREE TUI

> Gemini CLI-style terminal interface for free AI models via [GPT4Free](https://github.com/xtekky/gpt4free).
> No API key required to get started — with optional keys, custom endpoints, proxy routing and MCP tools when you want more.

```
  ██████╗ ██████╗ ████████╗██╗  ██╗███████╗██████╗ ███████╗███████╗
 ██╔════╝ ██╔══██╗╚══██╔══╝██║  ██║██╔════╝██╔══██╗██╔════╝██╔════╝
 ██║  ███╗██████╔╝   ██║   ███████║█████╗  ██████╔╝█████╗  █████╗
 ██║   ██║██╔═══╝    ██║   ╚════██║██╔══╝  ██╔══██╗██╔══╝  ██╔══╝
 ╚██████╔╝██║        ██║        ██║██║     ██║  ██║███████╗███████╗
  ╚═════╝ ╚═╝        ╚═╝        ╚═╝╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝
```

---

## ✨ Features

| Feature | Details |
|---------|---------|
| **Gemini CLI style TUI** | Dark theme, banner, status bar, modal pickers |
| **CLI one-shot mode** | `gpt4free -p "question"` like `gemini -p` |
| **Streaming responses** | Tokens appear in real-time |
| **Syntax highlighting** | Code blocks rendered with Pygments |
| **Provider/model picker** | Fuzzy-searchable modal dialogs |
| **Live status probing** | `/status` or `gpt4free status` to ping all providers |
| **Live model discovery** | `gpt4free models <provider>` fetches the provider's real-time model catalog |
| **Persistent settings** | Last provider + model auto-restored on next launch |
| **Prompt history** | ↑ ↓ arrows navigate previous prompts |

---

## 🚀 Installation (with uv)

```bash
# Install uv if needed
curl -Ls https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/your-user/gpt4free-tui
cd gpt4free-tui

uv sync          # install all dependencies
uv run gpt4free  # launch TUI
```

Optional extras:

```bash
uv sync --extra mcp    # adds the `mcp` package for real MCP server support
uv sync --dev          # adds pytest, ruff, mypy for development
```

---

## 📖 Usage

### TUI Mode
```bash
gpt4free                    # launch TUI (uses saved settings)
gpt4free --provider Blackbox --model gpt-4o   # override on launch
```

### CLI One-shot Mode (like Gemini `-p`)
```bash
gpt4free -p "Explain quantum computing"
gpt4free -p "Write a Python quicksort" --provider PollinationsAI --model deepseek-r1
gpt4free -p "Capital of France?" --no-stream   # print all at once
```

### Info Commands
```bash
gpt4free providers            # list all providers + model count
gpt4free providers --verbose  # show every model alias
gpt4free models <provider>    # fetch the LIVE model catalog straight from the provider's API
gpt4free status                # live-probe all providers (shows latency)
gpt4free config --show         # print current saved config
gpt4free config -P Blackbox -m gpt-4o           # change default provider/model
gpt4free config --proxy socks5://127.0.0.1:1080 # set an outbound proxy
gpt4free config --force-proxy                   # route ALL providers through the proxy
gpt4free config --clear-proxy                   # remove the configured proxy
```

## ⌨️ TUI Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Send message |
| `↑ / ↓` | Navigate prompt history |
| `Ctrl+P` | Pick provider |
| `Ctrl+M` | Pick model |
| `Ctrl+S` | Provider status table |
| `Ctrl+L` | Clear conversation |
| `Ctrl+N` | New session |
| `Ctrl+C` | Quit |

### In-chat Commands

| Command | Action |
|---------|--------|
| `/help` | Show command list |
| `/provider` | Pick provider |
| `/model` | Pick model |
| `/status` | Show provider status |
| `/clear` | Clear conversation |
| `/new` | New session |
| `/exit` | Quit |

> Keys, custom providers, and proxy settings are managed via the CLI (`gpt4free keys`, `gpt4free custom-providers`, `gpt4free config --proxy`) rather than in-chat.

---

## 🤖 Supported Providers & Models

| Provider | Auth | Notable Models |
|----------|------|-----------------|
| **PollinationsAI** | No auth | GPT-4o, GPT-4o Large, Mistral Large |
| **Qwen** | No auth | Qwen3.7 Plus/Max, Qwen3.6 Plus |
| **MetaAI** | No auth (proxy may be required) | Meta AI (Llama) |
| **Yqcloud** | No auth | GPT-4 |
| **Felo** | No auth | Felo Chat, Felo Search |
| **Pi** | No auth | Inflection Pi |
| **DeepInfra** | No auth | MiniMax M2.5 |
| **GeminiPro** | No auth (web session, proxy may be required) | Gemini 2.5 Flash |
| **OpenRouterFree** | No auth | OpenRouter Free Pool |
| **Groq** | No auth | GPT-OSS 120B |
| **Cerebras** | API key | Llama 3.3 70B, Llama 3.1 70B |
| **Gemini** | API key (proxy may be required) | Gemini 3.1 Pro, Gemini 3.5 Flash |
| **Grok** | API key (proxy may be required) | Grok 4, Grok 3 |
| **BlackboxPro** | API key | GPT-5, Claude Sonnet 4.5, DeepSeek R1 (proxied) |
| **HuggingFace** | API key | GPT-OSS 120B, GLM-5.2, DeepSeek V4 Flash/Pro, Qwen3.6 35B A3B |

No-auth providers work out of the box. Auth-gated providers need a key via `gpt4free keys --set`. Providers marked "proxy may be required" are geoblocked in some regions — configure one with `gpt4free config --proxy`. This table shows a curated, verified subset; run `gpt4free providers` for live status or `gpt4free models <provider>` for a provider's full current catalog.

---

## 📁 Project Structure

```
gpt4free-tui/
├── pyproject.toml              # uv / hatchling build config
├── README.md
├── src/gpt4free/
│   ├── __init__.py
│   ├── main.py                 # Typer CLI entrypoint (TUI, providers, models, status, config, keys, custom-providers)
│   ├── providers.py            # Curated provider registry + live probing + live model discovery
│   ├── chat.py                 # Async streaming chat session (+ tool-calling)
│   ├── render.py                # Rich markdown + syntax renderer
│   ├── tools.py                 # Local tool/skill registry (OpenAI function-calling schema)
│   ├── mcp_client.py            # Real MCP client (stdio + Streamable HTTP)
│   ├── config/
│   │   ├── __init__.py          # load_config / save_config
│   │   ├── app_config.py        # AppConfig dataclass (provider, model, keys, proxy, custom providers…)
│   │   ├── config_manager.py    # Reads/writes config file on disk
│   │   └── config_schema.py     # App name, config version, JSON schema
│   └── tui/
│       ├── __init__.py
│       ├── app.py                # Textual TUI application
│       └── widgets/
│           ├── __init__.py
│           ├── chat_log.py       # Scrollable chat widget
│           ├── pickers.py        # Provider + model modal pickers
│           ├── status.py         # Live provider status screen
│           ├── proxy.py          # Proxy configuration modal
│           └── keys_screen.py    # API key + custom provider modals
└── tests/
    ├── test_all_models.py
    ├── test_chat.py
    ├── test_main_cli.py
    ├── test_mcp_client.py
    ├── test_providers.py
    ├── test_tools.py
    ├── fixtures/
    │   └── dummy_mcp_server.py
    └── test_config/
        ├── test_api_keys_and_custom_providers.py
        ├── test_app_config.py
        ├── test_backward_compatibility.py
        ├── test_config_manager.py
        ├── test_performance.py
        └── test_proxy.py
```

## 🛠 Development

```bash
uv sync --dev          # install dev dependencies (ruff, mypy, pytest)
uv run ruff check .    # lint
uv run mypy src/       # type check
uv run pytest          # run tests
uv run pytest --cov    # run tests with coverage (min. 80%)
```

## ⚙️ Requirements

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) package manager
- Optional: `mcp` package for MCP server integration (`uv sync --extra mcp`)

---

## 📄 License

MIT
