# GitHub 10-Minute Start

This repo is designed so someone can download it from GitHub and get the
governed Node backend plus Nova Desktop running without hunting for extra
project files.

## What You Get

- `nova/` - local Python lawful runtime
- `nova/node` - governed Node backend, tool registry, receipts, replay, evidence, and manifests
- `desktop/` - Electron + Monaco desktop program
- `quickstart.ps1` - Windows one-command setup
- `quickstart.sh` - macOS/Linux one-command setup
- `.github/workflows/download-smoke.yml` - GitHub Actions proof that a fresh checkout installs and tests

## Option A: Download ZIP

1. Open the GitHub repo page.
2. Click **Code**.
3. Click **Download ZIP**.
4. Extract it somewhere writable.
5. Open a terminal in the extracted folder.

## Option B: Clone

```bash
git clone https://github.com/warheart1984-ctrl/agentic-coding-agent.git
cd agentic-coding-agent
```

If this is published under a different repo name, use that URL instead. The
scripts do not depend on the repo folder name.

## Windows

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\quickstart.ps1
```

The script installs the Python backend into `.venv`, installs the desktop npm
dependencies, verifies the backend, starts `python -m nova.api`, then launches
the desktop with `npm start`.

Useful manual commands:

```powershell
.\.venv\Scripts\python.exe -m nova.api
cd desktop
npm start
```

## macOS / Linux

```bash
chmod +x quickstart.sh bin/nova setup/*.sh
./quickstart.sh
```

The script installs the Python backend into `.venv`, installs the desktop npm
dependencies, verifies the backend, starts `python -m nova.api`, then launches
the desktop with `npm start`.

## Verify It Is Working

Backend:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/node/status
```

Desktop:

- Node URL should be `http://127.0.0.1:8080`.
- The heartbeat should show online.
- The tool registry should list `code` and `wire`.
- Receipts and replay/evidence surfaces should populate after a governed tool call.

## Ten-Minute Path

For a normal fresh machine with Python 3.10+ and Node.js 20+ already installed:

1. Download ZIP or `git clone`.
2. Run the matching quickstart script.
3. Wait for Python and npm installs.
4. Confirm `/node/status`.
5. Use Nova Desktop.

If Python or Node is missing, install those first:

- Python 3.12: https://www.python.org/downloads/
- Node.js 20 LTS: https://nodejs.org/

## Publish Rule

Commit source, docs, tests, package manifests, and lockfiles. Do not commit:

- `.venv/`
- `node_modules/`
- `.runtime/`
- generated `dist/`
- secrets or `.env` files
- compiled `.exe` installers unless explicitly requested
