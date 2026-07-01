# Lawful Nova Shell on macOS

This package is a source-only macOS shell distribution. It does not include
secrets, model weights, virtual environments, runtime logs, or generated desktop
build artifacts.

## Requirements

- macOS 13 or newer
- Xcode Command Line Tools
- Homebrew
- Python 3.10 or newer, with Python 3.12 recommended
- Node.js 20, installed by the bootstrap if `nvm` is available
- `zsh` or `bash`

## Install

From the extracted `lawful-nova-shell` folder:

```bash
chmod +x bin/nova setup/*.sh
setup/bootstrap.sh --non-interactive
```

The bootstrap creates or reuses `.venv`, installs the package in editable mode,
links the shell config, and writes `LAWFUL_NOVA_REPO_ROOT` into `~/.novarc`.

## Verify

```bash
setup/verify.sh
bin/nova health --json
```

The verifier checks the repo-local Python, the repo-local `bin/nova` shim,
configured Nova paths, optional Docker availability, and the in-process lawful
LLM health path.

## Daily Use

```bash
source ~/.zshrc
nova-chat
bin/nova run "summarize the current workspace"
```

If the Nova API is not already running, start the local API from another shell:

```bash
scripts/start-nova-stack.sh --api-only
```

## Apple Silicon Notes

NVIDIA GPU acceleration is Linux-only. On Apple Silicon, use local CPU or an
MPS-capable model backend and set this in `~/.novarc` when appropriate:

```bash
export NOVA_GPU_DEVICE="mps"
```

## Archive Contents

The macOS zip intentionally excludes:

- `.venv/`
- `.runtime/`
- `dist/`
- `desktop/`
- `node_modules/`
- `__pycache__/`
- local logs and secret files

The archive preserves executable bits for `bin/nova` and shell scripts.
