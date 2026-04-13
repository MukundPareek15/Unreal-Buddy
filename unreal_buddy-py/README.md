# UnrealBuddy

**An AI companion for Unreal Engine developers — watches your screen, answers questions via a floating text panel, and points at what it's describing.**

Built on top of [Clicky](https://github.com/farzaa/clicky) by Farza Majeed, ported to Windows and extended with an Unreal Engine knowledge base, web search/fetch tools, and a text-input interface (no microphone or voice API required — only an Anthropic key via Cloudflare Worker).

## How it works

1. Launch UnrealBuddy. A small blue triangle appears near your cursor.
2. Press **Ctrl+Alt** to open the floating input panel.
3. Type your Unreal Engine question and hit Enter.
4. UnrealBuddy screenshots your screen(s), sends them to Claude along with your question, and streams the answer back.
5. The companion cursor flies to the UI element Claude is describing.
6. Follow up — UnrealBuddy remembers the full conversation.

## Features

- **Floating text input** — Ctrl+Alt opens the panel, Escape closes it
- **Multi-monitor screen capture** sent to Claude for visual context
- **Cursor guidance** — companion flies to UI elements Claude references via POINT tags
- **Unreal Engine knowledge base** — blueprints, materials, lighting, animation docs injected automatically when UE is focused
- **Web search + URL fetch** — Claude can search DuckDuckGo or fetch Epic docs pages in real time (no API key needed)
- **Conversation memory** — 20-turn history so follow-up questions have full context
- **History window** — scrollable transcript accessible from the tray menu

## Prerequisites

- **Windows 10/11**
- **Python 3.12** — [download](https://www.python.org/downloads/)
- **uv** package manager — [install](https://docs.astral.sh/uv/getting-started/installation/)
- **Node.js 18+** — for deploying the Cloudflare Worker
- **Cloudflare account** (free tier) — [sign up](https://dash.cloudflare.com/sign-up)
- **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com)

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/unreal-buddy.git
cd unreal-buddy
```

### 2. Deploy the Cloudflare Worker

The Worker is a tiny proxy that holds your Anthropic API key. The app never touches the key directly.

```bash
cd worker
npm install
npx wrangler secret put ANTHROPIC_API_KEY
npx wrangler deploy
```

Copy the deployed URL (e.g. `https://unreal-buddy-proxy.your-subdomain.workers.dev`).

### 3. Install and run UnrealBuddy

```bash
cd clicky-py
uv sync
uv run python -m unreal_buddy
```

On first run, UnrealBuddy creates `%APPDATA%\UnrealBuddy\config.toml`. Open it and paste your Worker URL:

```toml
worker_url = "https://unreal-buddy-proxy.your-subdomain.workers.dev"
```

Restart UnrealBuddy. The blue triangle should appear near your cursor. Press Ctrl+Alt to open the input panel.

## Build a standalone exe

```bash
cd clicky-py
uv run pyinstaller unreal_buddy.spec
```

Output: `dist/unreal_buddy/UnrealBuddy.exe` — runs without Python installed.

## Configuration

Edit `%APPDATA%\UnrealBuddy\config.toml`:

| Field | Default | Description |
|-------|---------|-------------|
| `worker_url` | *(required)* | Your deployed Cloudflare Worker URL |
| `hotkey` | `ctrl+alt` | Open/close the input panel. Also supports `right_ctrl` |
| `default_model` | `claude-sonnet-4-6` | Claude model for responses |
| `log_level` | `INFO` | DEBUG, INFO, WARNING, or ERROR |
| `knowledge_dir` | `%APPDATA%/UnrealBuddy/knowledge/` | Path to knowledge base folder |

## Knowledge base

UnrealBuddy injects curated documentation into Claude's context based on which app is in the foreground. The Unreal Engine KB is included out of the box.

### Structure

```
knowledge/
  unreal_engine/
    _meta.toml          ← window title matchers
    overview.md
    blueprints.md
    materials.md
    lighting.md
    animation.md
    level_editing.md
```

### Adding a new app KB

Create a folder per app inside your knowledge directory:

```toml
# knowledge/my_app/_meta.toml
name = "My App"
window_titles = ["My App Title", "myapp.com"]
```

Drop `.md` files alongside it. No restart required — UnrealBuddy loads KB content fresh on every turn.

## Tests and linting

```bash
cd clicky-py
uv run pytest
uv run ruff check .
```

## Architecture

UnrealBuddy is a Python + PySide6 system tray app using asyncio (via qasync) for non-blocking I/O. The Anthropic API is proxied through a Cloudflare Worker.

**Key modules:**
- **CompanionManager** — central state machine orchestrating the text turn pipeline
- **CompanionWidget** — transparent cursor-following overlay with state-driven animations
- **TextInputWidget** — floating always-on-top panel for typed input and streamed responses
- **LLMClient** — Claude streaming via Anthropic SSE protocol with agentic tool-use loop
- **tools.py** — `web_search` (DuckDuckGo, no key) + `fetch_url` (httpx) tools
- **KnowledgeBase** — per-app markdown KB with window title matching and token-budgeted selection

**State flow:** IDLE → PROCESSING (screenshots + Claude + tools) → IDLE

## Credits

UnrealBuddy is built on top of [Clicky](https://github.com/farzaa/clicky) by [Farza Majeed](https://x.com/FarzaTV). All credit for the original concept, UX design, companion cursor behavior, and the POINT tag protocol goes to Farza. The Unreal Engine knowledge base, web search integration, text-input interface, and Windows-specific adaptations are original to UnrealBuddy.

## License

MIT — see [LICENSE](LICENSE).
