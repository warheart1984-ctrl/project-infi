# API Compatibility Bridge

This folder is the thin Vercel and compatibility entrypoint lane.

It does not own Jarvis runtime truth.

## Owns

- lightweight API entry wiring through [`index.py`](./index.py)
- compatibility packaging for environments that expect an `api/` surface

## Does Not Own

- canonical Jarvis runtime behavior in [`../src/api.py`](../src/api.py)
- workflow-shell authority in [`../app/main.py`](../app/main.py)

## External Suggestion Admission

This folder inherits the project-wide external suggestion admission law.

Outside proposals may be discussed or compared here, but they do not become
bridge truth unless project law has filtered them and the admitted form is
documented.

## Read Next

1. [../README.md](../README.md)
2. [../src/README.md](../src/README.md)
3. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
