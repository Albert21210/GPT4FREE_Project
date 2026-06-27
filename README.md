# GPT4FREE TUI

> Gemini CLI-style terminal interface for free AI models via [GPT4Free](https://github.com/xtekky/gpt4free).
> No API key required. Just ask.

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
| **Persistent settings** | Last provider + model auto-restored on next launch |
| **Prompt history** | ↑ ↓ arrows navigate previous prompts |
| **Only working providers** | Curated no-auth provider list |

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
gpt4free status               # live-probe all providers (shows latency)
gpt4free config --show        # print current saved config
gpt4free config -P Blackbox -m gpt-4o  # change default provider/model
```

---

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

---

## 🤖 Supported Providers & Models

| Provider | Notable Models |
|----------|----------------|
| **Blackbox** | GPT-4o |
| **PollinationsAI** | GPT-4o, GPT-4o Large, Mistral |

All providers work without API keys or account registration.

---

## 📁 Project Structure

```
gpt4free-tui/
├── pyproject.toml              # uv / hatchling build config
├── README.md
└── src/gpt4free/
    ├── __init__.py
    ├── main.py                 # Typer CLI entrypoint
    ├── providers.py            # Curated provider registry + probing
    ├── config.py               # Persistent user config
    ├── chat.py                 # Async streaming chat session
    ├── render.py               # Rich markdown + syntax renderer
    └── tui/
        ├── __init__.py
        ├── app.py              # Textual TUI application
        └── widgets/
            ├── __init__.py
            ├── chat_log.py     # Scrollable chat widget
            ├── pickers.py      # Provider + model modal pickers
            └── status.py       # Live provider status screen
```

---

## 🛠 Development

```bash
uv sync --dev          # install dev dependencies (ruff, mypy, pytest)
uv run ruff check .    # lint
uv run mypy src/       # type check
uv run pytest          # run tests
```

---

## ⚙️ Requirements

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) package manager

---

## 📄 License

MIT