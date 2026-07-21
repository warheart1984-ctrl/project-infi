---
title: Sovereign IDE
description: Runtime reference for the Sovereign IDE scaffold that backs the live desktop and visualizer pages.
---

# Sovereign IDE

The Sovereign IDE scaffold is the repository-local runtime slice for the five-core package under
`E:/project-infi/sovereign-ide`.

## Package shape

- `pyproject.toml`
- `sovereign_ide/app.py`
- `plugins/prime_architect.py`
- `runtime/orchestrator.py`
- `runtime/state.py`
- `runtime/federation_bootstrapper.py`
- `runtime/codex_loader.py`
- `ui/shell/sovereign_shell.py`

## Runtime contract

1. Load constitutional and conformance artifacts through the codex spine.
2. Bootstrap federation, epochs, lineage, and CAS-1 state.
3. Register the `sovereign.start` command with the IDE host and expose the `sovereign-ide` launcher.
4. Open the Sovereign Shell as the operator UI surface.
5. Keep the shared runtime context stable across the six documented surfaces.

## Launcher

- `sovereign-ide`
- `python -m sovereign_ide --bootstrap-only`

## Related views

- [Sovereign IDE visualizer](../visualizer/sovereign-ide.md)
- [Nova Shell](./nova-shell.md)
- [Runtime Core](./runtime-core.md)
- [Docs hub](../../docs/README.md)
