# Sovereign IDE Runtime Surface

The `sovereign-ide/` scaffold is the repository-local runtime slice for the Sovereign IDE concept.

## Package shape

- [pyproject.toml](../../sovereign-ide/pyproject.toml)
- [sovereign_ide/app.py](../../sovereign-ide/sovereign_ide/app.py)
- [plugins/prime_architect.py](../../sovereign-ide/plugins/prime_architect.py)
- [runtime/orchestrator.py](../../sovereign-ide/runtime/orchestrator.py)
- [runtime/state.py](../../sovereign-ide/runtime/state.py)
- [runtime/federation_bootstrapper.py](../../sovereign-ide/runtime/federation_bootstrapper.py)
- [runtime/codex_loader.py](../../sovereign-ide/runtime/codex_loader.py)
- [ui/shell/sovereign_shell.py](../../sovereign-ide/ui/shell/sovereign_shell.py)

## Runtime contract

1. Load constitutional and conformance artifacts through the codex spine.
2. Bootstrap federation, epochs, lineage, and CAS-1 state.
3. Register the `sovereign.start` command with the IDE host and expose the `sovereign-ide` launcher.
4. Open the Sovereign Shell as the operator UI surface.
5. Keep the shared runtime context stable across the six documented surfaces.

## Launcher

- `sovereign-ide`
- `python -m sovereign_ide --bootstrap-only`

## Navigation

- [Docs Hub](../README.md)
- [Architecture Tree](../architecture/README.md)
- [Docs-site runtime page](../../docs-site/docs/runtime/sovereign-ide.md)
- [Docs-site visualizer page](../../docs-site/docs/visualizer/sovereign-ide.md)
- [Package README](../../sovereign-ide/README.md)
