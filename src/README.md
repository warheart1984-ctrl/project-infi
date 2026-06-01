# Jarvis Runtime Spine

This folder contains the core AAIS/Jarvis runtime.

If a change affects routing, turn contracts, persona authority, governed repo
actions, verification, records, or cross-lane runtime law, it probably belongs
here.

## Owns

- core Jarvis runtime behavior in [`api.py`](./api.py)
- conversation/persona/continuity substrate in
  [`conversation_memory.py`](./conversation_memory.py)
- operator action and repo-change logic in
  [`jarvis_operator.py`](./jarvis_operator.py)
- Project Infi governed-cycle truth in
  [`project_infi_state_machine.py`](./project_infi_state_machine.py)
- law binding across runtime, repo changes, verification, and records in
  [`project_infi_law.py`](./project_infi_law.py)
- module governance, run logging, and shared governance law
- model/provider routing and bounded runtime lanes
- mission, memory, knowledge, and review state

## Does Not Own

- packaged launcher/package behavior in [`../aais/`](../aais/)
- workflow-shell hosting and packaged app mount in [`../app/`](../app/)
- frontend route composition and page rendering in [`../frontend/`](../frontend/)

## External Suggestion Admission

This runtime folder inherits the project-wide external suggestion admission
law.

Outside proposals may be compared, summarized, critiqued, or pressure-tested in
runtime work, but they do not become implementation truth here unless project
law has filtered them and the admitted form is documented.

## Start Here

- [`api.py`](./api.py)
  - main Jarvis runtime authority
- [`conversation_memory.py`](./conversation_memory.py)
  - persona mode, continuity filtering, and memory shaping
- [`jarvis_operator.py`](./jarvis_operator.py)
  - governed actions, repo-change flow, and runtime execution surfaces
- [`project_infi_state_machine.py`](./project_infi_state_machine.py)
  - governed cycle truth
- [`project_infi_law.py`](./project_infi_law.py)
  - shared law substrate for entry, action, outcome, and record
- [`module_governance.py`](./module_governance.py)
  - CISIV and module admission rules
- [`run_ledger.py`](./run_ledger.py)
  - run records, stage logs, and canonical log alignment

## Important Supporting Areas

- [`protocol/`](./protocol/)
  - protocol-adjacent helpers
- [`providers/`](./providers/)
  - provider-facing modules
- [`evolve/`](./evolve/)
  - evolve-law bridge and evolve-related support

## Read Next

1. [../README.md](../README.md)
2. [../app/README.md](../app/README.md)
3. [../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](../docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
4. [../docs/contracts/AAIS_DOC_PROTOCOL.md](../docs/contracts/AAIS_DOC_PROTOCOL.md)
5. [../docs/runtime/AAIS_SYSTEM_HANDBOOK.md](../docs/runtime/AAIS_SYSTEM_HANDBOOK.md)
6. [../docs/spine/AAIS_MASTER_SPEC.md](../docs/spine/AAIS_MASTER_SPEC.md)
