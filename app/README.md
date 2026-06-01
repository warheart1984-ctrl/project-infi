# AAIS Workflow Shell

This folder contains the FastAPI workflow/onboarding shell and the packaged app
host for AAIS.

It owns the shell layer around workflows, approvals, onboarding, packaged
frontend serving, and the compatibility bridge into the legacy Flask runtime.

It does not replace Jarvis runtime authority.

## Owns

- FastAPI shell startup and `/app` frontend hosting
- workflow and onboarding routes
- workflow persistence and run state
- workflow validation, templates, simulation, and recovery
- auth helpers and background task entrypoints
- the legacy bridge mount used to reach the canonical Flask/Jarvis runtime

## Does Not Own

- core Jarvis operator/runtime truth in [`../src/api.py`](../src/api.py)
- companion continuity semantics in
  [`../src/conversation_memory.py`](../src/conversation_memory.py)
- Project Infi governed-cycle truth in
  [`../src/project_infi_state_machine.py`](../src/project_infi_state_machine.py)
  and [`../src/project_infi_law.py`](../src/project_infi_law.py)

## Main Files

- [`main.py`](./main.py)
  - FastAPI shell, `/app` host, health surface, and legacy bridge mount
- [`config.py`](./config.py)
  - data paths, static bundle resolution, and environment defaults
- [`db.py`](./db.py)
  - workflow/onboarding persistence
- [`workflow_runtime.py`](./workflow_runtime.py)
  - workflow drafting, simulation, and runtime execution helpers
- [`workflow_validation.py`](./workflow_validation.py)
  - workflow graph validation and config building
- [`workflow_recovery.py`](./workflow_recovery.py)
  - stalled-run sweep and recovery behavior
- [`tasks.py`](./tasks.py)
  - background task entrypoints

## Current Authority Rule

- this folder owns the workflow/onboarding shell
- the shell may bridge into the Flask lane
- [`../src/api.py`](../src/api.py) still owns canonical Jarvis runtime truth

## External Suggestion Admission

This shell inherits the project-wide external suggestion admission law.

External workflow or product ideas may be discussed, compared, critiqued, or
pressure-tested here without becoming shell truth.

If an outside proposal is meant to change behavior, project law must admit the
filtered form before implementation or workflow mutation begins.

## Read Next

1. [../README.md](../README.md)
2. [../src/README.md](../src/README.md)
3. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
4. [../docs/runtime/AAIS_SYSTEM_HANDBOOK.md](../docs/runtime/AAIS_SYSTEM_HANDBOOK.md)
5. [../docs/contracts/AAIS_DOC_PROTOCOL.md](../docs/contracts/AAIS_DOC_PROTOCOL.md)
