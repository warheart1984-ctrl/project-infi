# Lawful Nova LLM Shell v1

Cross-platform shell and CLI for the **Local Lawful Nova** slice in [project-infi](https://github.com/warheart1984-ctrl/project-infi).

Nova Cortex here is the governed **Python runtime** under `nova/` — not a separate `nova.exe` binary. The shell wraps `python -m nova.cli` and starts the HTTP surfaces operators expect.

## Release v1 — what ships

| Component | Path | Platforms |
|-----------|------|-----------|
| CLI wrapper | `bin/nova` | Linux, macOS |
| CLI wrapper | `bin/nova.ps1` / `bin/nova.cmd` | Windows |
| Shell helpers | `setup/novrc.sh` | Linux, macOS |
| OS bootstrap | `setup/bootstrap.sh` | Linux, macOS |
| OS install | `setup/install_linux.sh` | Linux |
| OS install | `setup/install_macos.sh` | macOS |
| OS install | `setup/install_windows.ps1` | Windows |
| Stack installer | `setup/install_nova.sh` | Linux, macOS |
| Environment verify | `setup/verify.sh` | Linux, macOS |
| Environment verify | `setup/verify.ps1` | Windows |
| Stack config | `config/nova/nova-stack.json` | All |
| Shared bash library | `setup/lib/common.sh` | Linux, macOS |
| Standalone Python package | `pyproject.toml`, `nova/` | All |
| Parent-repo stack start | `../scripts/start-nova-stack.sh` | Linux, macOS (when embedded in project-infi) |
| Parent-repo stack start | `../scripts/start-nova-stack.ps1` | Windows (when embedded in project-infi) |

## Services and ports

| Service | Port | Health URL |
|---------|------|------------|
| Nova local API | 8080 | http://127.0.0.1:8080/health |
| Lawful brain | 8791 | http://127.0.0.1:8791/health |
| Operator kernel | 8790 | http://127.0.0.1:8790/health |
| AAIS (optional) | 8000 | http://127.0.0.1:8000/health |

## Prerequisites

From repo root:

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"    # Linux/macOS
# .venv\Scripts\pip install -e ".[dev]"   # Windows
```

Requires **Python 3.10+**.

### Standalone install (this directory)

```bash
cd lawful-nova-shell
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# OS tooling (pick one)
./setup/install_linux.sh    # Debian/Fedora/Alpine
./setup/install_macos.sh    # macOS + Homebrew

# Wire ~/.novarc and validate stack
./setup/bootstrap.sh
./setup/install_nova.sh
./setup/verify.sh
```

### Embedded in project-infi

### Linux / macOS (shared bash)

```bash
cd /path/to/project-infi
chmod +x lawful-nova-shell/bin/nova scripts/start-nova-stack.sh scripts/run_operator_kernel.sh

# Load shell helpers (nova-chat, novr, novstack, …)
source lawful-nova-shell/setup/novrc.sh

# Verify environment
./lawful-nova-shell/setup/verify.sh

# Health (in-process LawfulLLM + HTTP probes)
./lawful-nova-shell/bin/nova health --json

# Start Nova API + operator stack
./scripts/start-nova-stack.sh

# API only
./scripts/start-nova-stack.sh --api-only
```

### Windows (PowerShell)

```powershell
cd E:\project-infi

# Verify
powershell -NoProfile -ExecutionPolicy Bypass -File .\lawful-nova-shell\setup\verify.ps1

# Health
.\lawful-nova-shell\bin\nova.ps1 health --json

# Start stack
.\scripts\start-nova-stack.ps1

# API only
.\scripts\start-nova-stack.ps1 -ApiOnly
```

## Shell helpers (Linux / macOS)

After `source lawful-nova-shell/setup/novrc.sh`:

| Command | Action |
|---------|--------|
| `nova-chat [prompt]` | Local governed chat turn |
| `novr <prompt>` | One-shot run |
| `novtest` | Run verify + productization gate |
| `novpr` | Productization gate only |
| `novdoc` | Open productization status doc |
| `novsec` | JSON health snapshot |
| `novstack` | Start full Nova stack |

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LAWFUL_NOVA_REPO_ROOT` | auto-detected | Repo root |
| `NOVA_PORT` | `8080` | Nova API port |
| `NOVA_API_URL` | `http://127.0.0.1:8080` | API base URL |
| `NOVA_CORTEX_PATH` | `$REPO/nova` | Cortex runtime path |
| `NOVA_VOSS_RUNTIME_PATH` | `$REPO/nova` | Voss runtime path |
| `NOVA_RSL_PATH` | `$REPO/governance` | RSL / governance path |
| `NOVA_CLI` | `lawful-nova-shell/bin/nova` | CLI entrypoint |

## Productization gate

```bash
./.venv/bin/python scripts/nova_productization_gate.py
```

Expect `local_lawful_slice_ready: true` when Python runtime and in-process LawfulLLM pass. `local_services_ready: true` additionally requires operator services on 8790/8791 (and Nova API if you start the full stack).

## Stack config

[`config/nova/nova-stack.json`](config/nova/nova-stack.json) records ports and path templates. Paths use `${LAWFUL_NOVA_REPO_ROOT}` — no hard-coded drive letters. **Do not** point at vendor `nova.exe`; this repo uses the Python package at `nova/`.

## Troubleshooting

**Port 8080 in use** — CockroachDB Docker compose also binds 8080. Stop the container or set `NOVA_PORT=8081`.

**`Get-Process *nova*` finds nothing** — Expected. The API runs as `python -m nova.api`, not `nova.exe`.

**Health fails but CLI works** — In-process LawfulLLM may be fine; start the HTTP API with `start-nova-stack.sh --api-only`.

**Missing `.venv`** — Run `pip install -e ".[dev]"` from repo root.

## Tests

```bash
pytest tests/test_nova_productization.py -q
```

## Related docs

- [docs/runtime/NOVA_LAWFUL_PRODUCTIZATION.md](../docs/runtime/NOVA_LAWFUL_PRODUCTIZATION.md)
- [docs/runtime/NOVA_CORTEX.md](../docs/runtime/NOVA_CORTEX.md)
- [AGENTS.md](AGENTS.md) — agent behavior rules for Nova sessions

## Tag

**`lawful-nova-shell-v1`** — first cross-platform LLM shell release:

- Linux + macOS share one bash toolchain (`bin/nova`, `novrc.sh`, `verify.sh`, `common.sh`)
- Windows PowerShell parity (`nova.ps1`, `verify.ps1`, `bootstrap.ps1`)
- Standalone package (`pyproject.toml`) or embedded in [project-infi](https://github.com/warheart1984-ctrl/project-infi)
- Branch: `llm-nova-shell`
