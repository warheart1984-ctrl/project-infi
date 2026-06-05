# AAIS UL / CISIV Phases 1–5 Proof Packet

Claim: Ordinary chat turns, forge/repo contractors, and shared CISIV staging are wired through Project Infi with inspectable UL envelopes across Phases 1–5.

Claim status: **proven** on primary host (Windows 10, Python 3.10.11) with clean-runtime secondary profile parity (2026-06-05). See `docs/proof/aais-ul/FLAGSHIP_CROSS_MACHINE_MATRIX.md`. Full 1911-test pytest cross-host: **asserted pending**.

## 1) Incident / Issue ID

- ID: `UL-CISIV-P1-P5`
- Title: CISIV-aligned UL wiring across chat, forge, and repo paths
- Scope: Phases 1–5 rollout (chat envelope, modular generation, admission, forge/repo governance, CISIV consolidation)
- Severity: governance / runtime visibility
- Linked docs:
  - `docs/contracts/AAIS_UL_DOCTRINE.md`
  - `docs/runtime/AAIS_SUBSYSTEM_SPEC.md`
  - `ProjectInfinity_UL_Documentation.pdf`

## 2) Hypothesis And Root Cause

- Initial hypothesis: UL was implemented in layers but not on every runtime path; CISIV stage constants were duplicated.
- Confirmed root cause: chat generation, admission, forge handoffs, and ledger/governance each carried partial or duplicate CISIV/UL wiring.
- Why credible: drift/smoke tooling and targeted pytest covered each phase surface independently.
- Trigger conditions: ordinary chat turn, forge contractor call, patch review lifecycle, run ledger write.

## 3) Reproduction Steps (Pre-fix signal)

1. Send `/api/chat/sessions/{id}/message` — no top-level `ul_substrate` / modular preview on all paths.
2. Forge and evolve calls — inconsistent Project Infi `law_enforcement` at AAIS orchestration layer.
3. Inspect `module_governance.py` and `run_ledger.py` — duplicate CISIV constants and normalizers.

Expected failure signal: missing `ul_substrate`, missing admission metadata, divergent stage names (`verify` vs `verification`).

## 4) Fix Details (What / Why / How)

| Phase | Deliverable | Primary modules |
|---|---|---|
| 1 | Chat runtime `ul_substrate` envelope | `src/api.py`, `src/chat_turn_governance.py` |
| 2 | Single modular UL generation path | `src/api.py`, `src/chat_turn_governance.py` |
| 3 | Ordinary-turn Project Infi admission | `finalize_chat_turn_admission()` |
| 4 | Forge/evolve/patch governed cycle | `src/forge_repo_governance.py`, `src/jarvis_operator.py` |
| 5 | Canonical CISIV source | `src/cisiv.py`, `module_governance`, `run_ledger` |

Risks / mitigations:
- JSON circular refs from modular preview → bounded export in `wrap_chat_runtime_payload()`.
- Double `require_contract` on forge paths → single `finalize_contractor_runtime_action()` helper.

## 5) Verification Evidence

### One-click override command

```bash
python -m pytest tests/test_cisiv.py tests/test_run_ledger_cisiv.py tests/test_chat_turn_governance.py tests/test_forge_repo_governance.py tests/test_module_governance.py tests/test_api.py -k "ul_substrate_envelope or modular_preview or project_infi_admission or run_ledger_routes" -q && python -m tools.ul.drift && python -m tools.ul.smoke
```

### Commands (2026-05-29 UTC session)

```text
python -m tools.ul.drift
python -m tools.ul.smoke
python -m pytest tests/test_cisiv.py tests/test_run_ledger_cisiv.py tests/test_chat_turn_governance.py tests/test_forge_repo_governance.py tests/test_module_governance.py tests/test_jarvis_operator.py::TestJarvisOperator::test_request_forge_code_wraps_result_with_auto_approve_flag tests/test_jarvis_operator.py::TestJarvisOperator::test_request_evolution_job_wraps_result_with_hall_tracking -q
python -m pytest tests/test_api.py -k "ul_substrate_envelope or modular_preview or project_infi_admission or run_ledger_routes" -q
```

### Outputs

```text
tools.ul.drift:
  missing_from_adapters: []
  adapter_count: 57

tools.ul.smoke:
  overall_ok: true
  sample_count: 26
  failed_samples: 0
  pytest (embedded): 57 passed

pytest unit gate (28 tests):
  28 passed in 2.74s

pytest api gate (8 tests):
  8 passed in 13.90s
```

Environment: Windows 10 (10.0.19045), Python 3.10.11.

Post-commit record:

```text
git rev-parse HEAD
7b4e8060621a5b0a642be7671688c22f2fa27fb4
git log -1 --format=%H%n%s
7b4e8060621a5b0a642be7671688c22f2fa27fb4
Wire AAIS UL/CISIV phases 1-5 across chat, forge, and repo paths.
```

## 6) Hardware Matrix

| Machine | Role | OS | Python | Test set | Outcome | Evidence |
|---|---|---|---|---|---|---|
| desktop-primary | primary | Windows 10 | 3.10.11 | UL/CISIV core + drift/smoke + naming + genome + memory gateway | pass | `.runtime/cross_machine_matrix/primary-desktop-00i57qv.json` |
| desktop-clean-runtime | secondary | Windows 10 | 3.10.11 | Same gate set, isolated `AAIS_DATA_DIR` | pass | `.runtime/cross_machine_matrix/secondary-desktop-00i57qv.json` |
| dev-linux | secondary (physical) | — | — | not run | asserted pending | WSL blocked (no pytest); operator host required |
| dev-macos | secondary (physical) | — | — | not run | asserted pending | — |

Matrix comparison: `.runtime/cross_machine_matrix/matrix_comparison.json` — **matrix_passed: true** (2026-06-05).

## 7) Time / Author / Sign-Off

- Start time (UTC): 2026-05-28 (multi-session rollout)
- End time (UTC): 2026-05-29
- Author: Cursor agent (user-directed)
- Reviewer: pending human review
- Sign-off decision:
  - [ ] Asserted (insufficient proof)
  - [x] Proven (single-machine evidence complete)
  - [ ] Rejected
- Notes: UL/CISIV gate matrix proven across primary + clean-runtime secondary (2026-06-05). Full pytest cross-host remains operator debt.
