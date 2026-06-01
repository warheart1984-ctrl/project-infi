# AI Mechanic Invariant Catalog (STAGE1)

Diagnostic families:

| Family | Scope |
|--------|--------|
| **GOV** | Governance, ownership, exception surfacing, rollback, provenance |
| **RNT** | Runtime loops, validation, audit hooks, tools, trace |
| **CST** | Cost / redundant model calls / tool ceilings |
| **HUM** | Human control, HITL, Stage 2 usurpation/leakage in prompts |

## Seed codes (18)

| Code | Summary |
|------|---------|
| GOV-01 | Missing decision owner |
| GOV-12 | AI decision without exception path |
| GOV-15 | Ungoverned prompt asset |
| GOV-20 | Shadow workflow duplicate |
| GOV-25 | High-impact workflow missing rollback metadata |
| GOV-30 | Genome missing extraction provenance |
| RNT-04 | Agent self-loop / cycle risk |
| RNT-08 | Missing output validation |
| RNT-11 | Model call without audit hook |
| RNT-15 | Tool binding without constraints |
| RNT-20 | Trace tool without audit/constraints |
| RNT-22 | Model chain missing validates edges |
| CST-07 | Redundant model calls |
| CST-09 | CI LLM without cost center |
| CST-12 | Tool calls without cost ceiling |
| HUM-03 | Human control removed / Stage 2 usurpation in prompt |
| HUM-05 | High-impact workflow missing HITL |
| HUM-08 | Unauthorized actuation language in prompt |

Stage 2 fidelity detectors (`src/stage2_fidelity_metrics.py`) are wired against prompt asset file content in `check_prompt_stage2_fidelity`.

Machine catalog: `mechanic/invariants/ai_workflow_invariants.v1.json`

Fixtures:

- v1: `mechanic/fixtures/sample-customer-repo/`
- v2: `mechanic/fixtures/sample-customer-repo-v2/`
