# Sovereign IDE

`sovereign-ide/` is the scaffold for the five-core Sovereign IDE runtime slice:

- `plugins/prime_architect.py`
- `runtime/orchestrator.py`
- `runtime/federation_bootstrapper.py`
- `runtime/codex_loader.py`
- `ui/shell/sovereign_shell.py`

## What this package does

- Boots constitutional artifacts through `CodexLoader`
- Starts federation and epoch bootstrap through `FederationBootstrapper`
- Exposes a `PrimeArchitectPlugin` entrypoint for an IDE host
- Opens a PyQt6 `SovereignShell` with the six documented operator surfaces when the UI is available
- Serves the guide-aligned HTTP API hooks for timeline, shader, organism, consensus, ledger, and audio
- Provides launcher commands for `sovereign-ide` and `python -m sovereign_ide --bootstrap-only`

## Where to read next

- [Repository docs hub](../docs/README.md)
- [Sovereign IDE runtime surface](../docs/runtime/sovereign-ide.md)
- [Docs-site runtime page](../docs-site/docs/runtime/sovereign-ide.md)
- [Docs-site visualizer page](../docs-site/docs/visualizer/sovereign-ide.md)

## Run the scaffold

```bash
cd sovereign-ide
python main.py
```

You can also launch the packaged entrypoints:

```bash
sovereign-ide
python -m sovereign_ide --bootstrap-only
python -m sovereign_ide --serve-api --api-port 8787
```

If PyQt6 is available, the shell window opens; otherwise the fallback mode prints a short runtime summary.
