# AAIS Launcher Package

This folder contains the cross-platform launcher package for AAIS.

It owns startup, bundle preparation, data-dir resolution, and desktop-style
app checks.

It does not own Jarvis runtime semantics.

## Owns

- `python -m aais` entrypoints
- project-root discovery
- frontend build preparation and staging into `app/static/`
- per-platform user data-dir selection
- `uvicorn` startup for the packaged shell
- desktop readiness checks through `doctor`

## Does Not Own

- core Jarvis runtime truth in [`../src/api.py`](../src/api.py)
- workflow-shell behavior in [`../app/main.py`](../app/main.py)
- frontend route semantics in [`../frontend/src/App.jsx`](../frontend/src/App.jsx)

## External Suggestion Admission

This launcher folder inherits the project-wide external suggestion admission
law.

Outside proposals may influence comparison or packaging discussion here, but
they do not become launcher truth unless project law has filtered them and the
admitted form is documented.

## Main Files

- [`__main__.py`](./__main__.py)
  - module entrypoint for `python -m aais`
- [`launcher.py`](./launcher.py)
  - implements `start`, `prepare`, and `doctor`

## Main Commands

```bash
python -m aais start --data-dir ./.runtime/aais-data
python -m aais prepare --force-build --data-dir ./.runtime/aais-data
python -m aais doctor --data-dir ./.runtime/aais-data
```

Legacy note:

- [`../start_jarvis.py`](../start_jarvis.py) now forwards to this launcher path

## Read Next

1. [../README.md](../README.md)
2. [../app/README.md](../app/README.md)
3. [../src/README.md](../src/README.md)
4. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
5. [../docs/runtime/AAIS_SYSTEM_HANDBOOK.md](../docs/runtime/AAIS_SYSTEM_HANDBOOK.md)
