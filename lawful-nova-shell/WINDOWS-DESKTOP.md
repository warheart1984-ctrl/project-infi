# Nova Desktop for Windows

This archive contains the Windows desktop program source and the governed Nova
Node backend. It is source-only: no `.exe`, no bundled Node.js runtime, no
`node_modules`, and no local runtime receipts.

## What Is Included

- `desktop/` - Electron + Monaco desktop application
- `desktop/package-lock.json` - repeatable npm install input
- `nova/` - Python lawful runtime
- `nova/node/` - governed Node routes, tools, receipts, replay, evidence, and manifests
- `setup/bootstrap.ps1` - Windows bootstrap
- `setup/verify.ps1` - Windows verifier
- `policy.yaml`, `pyproject.toml`, and requirements files

## Install

From the extracted `nova-desktop-windows` folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
cd desktop
npm install
```

If `py` is unavailable, use any Python 3.10+ interpreter and keep the `.venv`
folder at the archive root.

## Start The Governed Node

From the archive root:

```powershell
.\.venv\Scripts\python.exe -m nova.api
```

That command is the local equivalent of `python -m nova.api` using the archive
virtual environment.

The Node API defaults to `http://127.0.0.1:8080`. Nova Desktop can point at
that URL from its settings strip.

## Start The Desktop Program

From `desktop/`:

```powershell
npm start
```

## Verify

From the archive root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup\verify.ps1
.\.venv\Scripts\python.exe -m pytest tests -q
cd desktop
npm test
```

## Build An Installer Later

The source includes `desktop/installer-config.json`.

```powershell
cd desktop
npm install
npm run build:win
```

If this source is nested under a parent workspace that declares another package
manager, build from the extracted zip root so Electron Builder sees the desktop
project directly.
