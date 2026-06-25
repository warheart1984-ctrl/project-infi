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

## Reasoning Profile

AAIS reasoning uses the canonical
[`AAIS_REASONING_PROFILE.md`](../docs/contracts/AAIS_REASONING_PROFILE.md)
handshake for governed conclusions, CCS evidence references, declared
assumptions, bounded uncertainty, invariant checks, continuity impact, and
DAR-Z/DZI-1 interoperability.

CCS identity, event, evaluation, evidence, continuity-trace, and Theta
registration objects are specified in
[`CCS_CORE_SCHEMA.md`](../docs/contracts/CCS_CORE_SCHEMA.md) and
[`ccs_core_objects.v1.json`](../schemas/ccs_core_objects.v1.json).
The first AAIS + CSLEIS continuity harness is
[`test_ccs_continuity_harness.py`](../tests/test_ccs_continuity_harness.py).

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

## Read Next

1. [../docs/operators/AAIS_OPERATOR_GUIDE.md](../docs/operators/AAIS_OPERATOR_GUIDE.md) — **operators: start here**
2. [../README.md](../README.md)
3. [../app/README.md](../app/README.md)
4. [../src/README.md](../src/README.md)
5. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
6. [../docs/contracts/AAIS_REASONING_PROFILE.md](../docs/contracts/AAIS_REASONING_PROFILE.md)
7. [../docs/contracts/CCS_CORE_SCHEMA.md](../docs/contracts/CCS_CORE_SCHEMA.md)
8. [../tests/test_ccs_continuity_harness.py](../tests/test_ccs_continuity_harness.py)
