# AI Mechanic STAGE1 Proof Bundle

| Field | Value |
|-------|-------|
| **Subsystem** | AI Mechanic post-MVP hardening |
| **Claim** | `asserted` (single-machine pytest + governance gate) |
| **Date** | 2026-05-31 |
| **Prior stage** | [STAGE0_PROOF_BUNDLE.md](./STAGE0_PROOF_BUNDLE.md) |

## What STAGE1 adds over STAGE0

- **18 invariant catalog** entries (GOV/RNT/CST/HUM) with Stage 2 fidelity detectors on prompt assets
- **Second fixture** `sample-customer-repo-v2` (MCP unconstrained, shadow workflow, trace cycle, no HITL on high-impact CI)
- **trace_ndjson adapter** (`--trace-path`, `MECHANIC_TRACE_PATH`)
- **MECH-CHAT-01** runtime profile hook in `src/api.py` (feature-flagged)
- **MECH-APPLY-01** review-gated `apply-review --create-review` (never writes customer repo)
- **Report mode** (`--mode report`) markdown operator summary
- **Cross-machine replay lane** stub (inactive until operator fills manifest)
- **Trust Bundle stub** ([TRUST_BUNDLE.md](./TRUST_BUNDLE.md))
- **Dogfood report** ([dogfood/MECHANIC_DOGFOOD_REPORT.md](./dogfood/MECHANIC_DOGFOOD_REPORT.md))

## What is proven (asserted)

- STAGE0 capabilities remain (scan/diagnose/rebuild dry-run, apply blocked, enforcer)
- v1 and v2 fixtures produce distinct drift profiles
- Trace ingest adds nodes/edges to genome
- Chat hook returns 403 on profile violation when `MECHANIC_ENFORCE_PROFILE=1`
- apply-review creates patch review records only

## Verification

```bash
pytest tests/test_mechanic.py tests/test_mechanic_chat_hook.py -q
python .github/scripts/check-mechanic-governance.py
make mechanic-gate
```

## Fixtures

| Repo | Profile |
|------|---------|
| `mechanic/fixtures/sample-customer-repo/` | missing HITL, redundant model calls (v1) |
| `mechanic/fixtures/sample-customer-repo-v2/` | MCP, shadow workflow, cycle, high-impact CI (v2) |
| `mechanic/fixtures/traces/sample_trace.ndjson` | shared trace ingest sample |

## Debt (partially closed)

| ID | STAGE1 status |
|----|---------------|
| MECH-TRACE-01 | partially closed — NDJSON adapter |
| MECH-APPLY-01 | partially closed — review-gated only |
| MECH-CHAT-01 | partially closed — feature-flag hook |
| MECH-XM-01 | stub manifest only |
| MECH-LLM-01 | debt |
| MECH-TRIBAL-01 | debt |
