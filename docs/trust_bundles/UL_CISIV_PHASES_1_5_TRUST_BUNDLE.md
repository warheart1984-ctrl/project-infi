# Trust Bundle — UL / CISIV Phases 1–5

Normative schema: `docs/TRUST_BUNDLE_SPEC.md`

```text
claim_label: proven
why_short: |
  Phases 1–5 wire chat UL envelopes, modular generation, Project Infi admission,
  forge/repo governance, and canonical CISIV helpers with passing drift/smoke and pytest gates.
  Gate matrix proven across primary + clean-runtime secondary profiles (2026-06-05).
  Full 1911-test pytest cross-host rerun remains asserted debt.
proof_links:
  - docs/proof/aais-ul/UL_CISIV_PHASES_1_5_PROOF.md
  - docs/proof/aais-ul/FLAGSHIP_CROSS_MACHINE_MATRIX.md
  - docs/proof/aais-ul/cross_machine/REPLAY_MANIFEST.v1.json
  - .runtime/cross_machine_matrix/matrix_comparison.json
  - docs/contracts/AAIS_UL_DOCTRINE.md
  - src/chat_turn_governance.py
  - src/forge_repo_governance.py
  - src/cisiv.py
none_yet: false
override_command: python -m pytest tests/test_cisiv.py tests/test_run_ledger_cisiv.py tests/test_chat_turn_governance.py tests/test_forge_repo_governance.py tests/test_module_governance.py tests/test_api.py -k "ul_substrate_envelope or modular_preview or project_infi_admission or run_ledger_routes" -q && python -m tools.ul.drift && python -m tools.ul.smoke
override_breaks_blueprint: false
debt_ticket_ref: none
created_at_utc: 2026-05-29T04:00:00Z
updated_at_utc: 2026-06-05T18:30:00Z
author: cursor-agent
context: AAIS UL/CISIV phased rollout commit (Phases 1–5)
```
