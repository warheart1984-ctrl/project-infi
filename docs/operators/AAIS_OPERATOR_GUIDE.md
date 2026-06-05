# AAIS Operator Guide

Simple instructions for local use, offline use, and standalone desktop builds.

**Audience:** operators who want to run AAIS on their own machine without reading the full developer docs.

---

## 1. What AAIS Is

AAIS is a **local-first AI runtime**.

- You run it on **your** computer.
- You control the **API keys**.
- You choose which **AI providers** AAIS can call.
- A **web browser is optional** — you can use the terminal or a packaged desktop window instead.

Your data and keys stay on your machine unless you explicitly connect to a cloud AI provider.

---

## 2. First-Time Setup (3 Steps)

### Step 1 — Install

```bash
git clone https://github.com/warheart1984-ctrl/Project-Infinity1.git
cd Project-Infinity1
python -m pip install -e ".[dev]"
```

On Windows PowerShell, use the same commands (Python 3.10+ required).

**Node.js (optional):** Only needed if you rebuild the frontend (`npm run build` in `frontend/`) or run frontend unit tests (`npm run test:ci`). Packaged operators can skip Node entirely — use `python -m aais prepare` instead. Verify with `node -v` and `npm -v` (Node 18+). Install from [nodejs.org](https://nodejs.org/) if those commands are missing on Windows.

### Step 2 — Add your AI keys (optional)

Copy the template and edit only the keys you need:

```bash
cp .env.example .env
```

Open `.env` in any text editor. Leave blank any provider you do not use.

**No keys?** Use mock mode (see [Start without keys](#start-without-api-keys-mock-mode)).

### Step 3 — Prepare the app bundle

```bash
python -m aais prepare --data-dir ./.runtime/aais-data
python -m aais doctor --data-dir ./.runtime/aais-data
```

`prepare` stages the UI into `app/static/`. `doctor` prints a health summary so you can see if anything is missing.

---

## 3. How to Start AAIS

### Normal start (opens browser when ready)

```bash
python -m aais start --data-dir ./.runtime/aais-data
```

When the server is healthy, your browser opens to the app shell.

### Start without opening a browser

```bash
python -m aais start --data-dir ./.runtime/aais-data --no-browser
```

Use this for terminal-only use or when building a desktop EXE.

### Start without API keys (mock mode)

```bash
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
```

Mock mode gives deterministic local replies — useful for testing with no cloud keys.

### Where to go in the browser (if you use the UI)

| What | URL |
|------|-----|
| Health check | http://127.0.0.1:8000/health |
| App home | http://127.0.0.1:8000/app |
| Jarvis console | http://127.0.0.1:8000/app/jarvis |
| Jarvis API | http://127.0.0.1:8000/api/... |

Legacy mount `/legacy_api/api/...` remains for compatibility; the UI uses `/api/...` on the same host.

Default port is **8000** (not 8790). Change with `--port 9000` if needed.

### Workflow approvals (optional)

**Jarvis chat works without Redis.** The workflow shell (queued runs, Celery jobs, `/workflows/approvals`, OTEM execution approvals) needs Redis and optionally a Celery worker.

1. Copy `.env.example` to `.env` — Redis defaults to `127.0.0.1:6379`.
2. Start Redis locally or via Docker.
3. Check reachability: `curl -fsS http://127.0.0.1:8000/health/details` — look for `"redis_reachable": true`.

Docker Compose deployments override `REDIS_URL` with the service hostname `redis`; bare-metal local start uses `127.0.0.1` by default.

### ARIS standalone (optional)

ARIS is an admission/truth layer. By default it runs **embedded** inside AAIS.

**Standalone ARIS service** (separate process on port 8791):

```bash
# Terminal 1 — ARIS service
python -m aris_service

# Terminal 2 — AAIS using standalone ARIS
set ARIS_MODE=standalone
python -m aais start --data-dir ./.runtime/aais-data
```

On Linux/macOS, use `export ARIS_MODE=standalone` instead of `set`.

**Dual mode** (try standalone first, fall back to embedded):

```bash
set ARIS_MODE=dual
python -m aais start --data-dir ./.runtime/aais-data
```

Or add `ARIS_MODE=dual` to your `.env` file.

---

## 4. How to Add Your AI Keys

AAIS reads keys from your **`.env` file** (recommended) or from **environment variables**.

After changing keys, **restart AAIS**.

### Recommended: edit `.env`

Copy `.env.example` to `.env` and set only what you use. Example:

```env
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-gemini-key
```

### Common providers

| Provider | Key variable | Optional model variable |
|----------|--------------|-------------------------|
| OpenAI | `OPENAI_API_KEY` | `AAIS_OPENAI_MODEL` (default `gpt-4o-mini`) |
| Claude | `ANTHROPIC_API_KEY` | `AAIS_CLAUDE_MODEL` |
| Google Gemini | `GOOGLE_API_KEY` or `GEMINI_API_KEY` | `AAIS_GEMINI_MODEL` |
| Mistral | `MISTRAL_API_KEY` | `AAIS_MISTRAL_MODEL` |
| DeepSeek | `DEEPSEEK_API_KEY` | `AAIS_DEEPSEEK_MODEL` |
| NVIDIA Nemotron | `NVIDIA_API_KEY` | `AAIS_NVIDIA_MODEL` |
| xAI (Grok) | `XAI_API_KEY` | `AAIS_XAI_MODEL` |
| Groq | `GROQ_API_KEY` | `AAIS_GROQ_MODEL` |
| OpenRouter | `OPENROUTER_API_KEY` | `AAIS_OPENROUTER_MODEL` |
| Local (no cloud) | *(none)* | use `--preset mock` or `--preset laptop` |

Full list: [docs/providers/FRONTIER_MODEL_ADAPTERS.md](../providers/FRONTIER_MODEL_ADAPTERS.md) and [`.env.example`](../../.env.example).

### Windows PowerShell (alternative to `.env`)

```powershell
$env:OPENAI_API_KEY = "your-key-here"
$env:ANTHROPIC_API_KEY = "your-key-here"
python -m aais start --data-dir ./.runtime/aais-data
```

### Linux / macOS (alternative to `.env`)

```bash
export OPENAI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
python -m aais start --data-dir ./.runtime/aais-data
```

### Verify keys are active

With AAIS running:

```bash
curl -fsS http://127.0.0.1:8000/legacy_api/api/jarvis/providers
```

Each provider shows `"available": true` when its key is set and valid.

---

## 5. How to Use AAIS

### With the web UI

1. Start AAIS (browser opens automatically, or go to http://127.0.0.1:8000/app/jarvis).
2. Chat, upload files, and open dashboards from the Jarvis console.

### Without the web UI (terminal + API)

Start with `--no-browser`, then use curl or the helper menu:

**Windows:** `.\scripts\operator_menu.ps1`  
**Linux/macOS:** `./scripts/operator_menu.sh`

Or run these commands yourself:

```bash
# Health
curl -fsS http://127.0.0.1:8000/health

# Create a chat session
curl -fsS -X POST http://127.0.0.1:8000/legacy_api/api/chat/sessions \
  -H "Content-Type: application/json" \
  -d "{\"system_prompt\":\"You are Jarvis.\"}"

# Send a message (replace SESSION_ID)
curl -fsS -X POST http://127.0.0.1:8000/legacy_api/api/chat/sessions/SESSION_ID/message \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"Hello\",\"response_mode\":\"operator\"}"
```

### Useful status endpoints (governance / subsystems)

| Check | URL |
|-------|-----|
| Capability bridge | http://127.0.0.1:8000/legacy_api/api/jarvis/capability-bridge/status |
| Memory board | http://127.0.0.1:8000/legacy_api/api/jarvis/memory/board |
| ARIS boundary | http://127.0.0.1:8000/legacy_api/api/jarvis/aris-boundary/status |
| OTEM bounded | http://127.0.0.1:8000/legacy_api/api/jarvis/otem-bounded/status |
| Governed pipeline | http://127.0.0.1:8000/legacy_api/api/jarvis/pipeline/TURN_ID |
| Providers | http://127.0.0.1:8000/legacy_api/api/jarvis/providers |

---

## 6. Desktop App (No Browser Required)

You build the desktop app **on your own machine**. EXE files are **not** stored on GitHub — share them via USB or file share.

### Prerequisites

```bash
python -m pip install -e ".[dev,desktop]"
```

### Option A — Terminal-only app (simplest)

Starts AAIS in the background; use the operator menu or curl.

**Windows:**

```powershell
.\scripts\build_desktop_terminal.ps1
# Output: dist\aais_terminal.exe
```

**Linux:**

```bash
chmod +x scripts/build_desktop_terminal.sh
./scripts/build_desktop_terminal.sh
# Output: dist/aais_terminal
```

Run the built file. Data is stored next to the executable in `.runtime/aais-data`.

### Option B — Desktop window (feels like an app)

Opens a local window (pywebview) — no separate browser tab.

**Windows:**

```powershell
.\scripts\build_desktop_window.ps1
# Output: dist\aais_desktop.exe
```

**Linux:**

```bash
chmod +x scripts/build_desktop_window.sh
./scripts/build_desktop_window.sh
# Output: dist/aais_desktop
```

Still runs entirely on your machine. Nothing is sent to the cloud except when you use a cloud AI key.

### Build troubleshooting

| Problem | Fix |
|---------|-----|
| Port 8000 in use | Stop other AAIS instances or use `--port 9000` |
| UI missing | Run `python -m aais prepare --data-dir ./.runtime/aais-data` before building |
| PyInstaller not found | `pip install pyinstaller` or `pip install -e ".[desktop]"` |
| Keys not working in EXE | Place a `.env` file next to the executable |

---

## 7. Operator Safety Notes

- **Keys stay local** — stored in your `.env` or OS environment, not uploaded to GitHub.
- **No telemetry** — AAIS does not phone home by default.
- **You choose providers** — only keyed providers are activated.
- **Governance is active** — unsafe execution paths are blocked by default.
- **OTEM execution** requires operator approval before apply.
- **Dreamspace** is opt-in only (off by default).
- **Do not commit `.env` or `dist/`** — both are gitignored.

---

## Quick reference

```bash
# Install
python -m pip install -e ".[dev]"

# Keys
cp .env.example .env   # edit keys

# Prepare + check
python -m aais prepare --data-dir ./.runtime/aais-data
python -m aais doctor --data-dir ./.runtime/aais-data

# Start (browser)
python -m aais start --data-dir ./.runtime/aais-data

# Start (no browser, mock)
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser

# Help
python -m aais --help
```

For developers and subsystem details, see [README.md](../../README.md) and [AAIS_SUBSYSTEM_SPEC.md](../runtime/AAIS_SUBSYSTEM_SPEC.md).
