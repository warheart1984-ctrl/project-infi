# Local Runtime Data

This folder holds local runtime state and rebuildable support data.

It is a state root, not a runtime authority surface.

## Contains

- [`jarvis.db`](./jarvis.db)
  - local runtime persistence
- [`chroma/`](./chroma/)
  - local vector or retrieval support state

## Handling Rule

- treat this folder as local state, not canonical source code
- document schema or retention changes before changing storage expectations

## External Suggestion Admission

This folder inherits the project-wide external suggestion admission law.

Outside storage or state proposals may be compared here, but they do not become
data-policy truth unless project law has filtered them and the admitted form is
documented.

## Read Next

1. [../README.md](../README.md)
2. [../src/README.md](../src/README.md)
3. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
