# CORI Alpha Stewardship–Runtime Alignment

This document makes explicit how steward roles map to runtime responsibilities and evidence obligations.

## Steward roles

### Cognitive / Architectural Steward (Jon)

**Runtime responsibilities**

- API and data model design (`app/main.py`, `src/governed/`, OpenAPI specs)
- State transition logic (`make_governed_mission`, bridge modules)
- Invariant definitions (`src/cori/governance_invariants.py`)

**Evidence responsibilities**

- Architecture decisions recorded as `evidence_attached` artifacts or ADR-linked continuity events
- Change logs for runtime behavior (schema migrations, bridge contract changes)
- Sign-off on invariant test suites (`tests/test_runtime_governance_invariants.py`)

**Runtime mirror**

- Code: `src/governed/`, `src/cori/`, `nova/bridges/`
- Behavior: governed mission spine, envelope fields, chain ordering
- Evidence: `panel_emitted`, `law_eval`, schema/version metadata in asset registry

---

### Execution Steward (Daniel)

**Runtime responsibilities**

- Deployment, infrastructure, performance
- CI/CD, observability, reliability
- Docker Compose, AAIS/Nova/AAES process orchestration

**Evidence responsibilities**

- Deployment manifests as `evidence_attached` (or import-type evidence)
- Incident reports, SLO/SLA metrics as continuity events
- Test runs and build artifacts linked to `asset:deployment:{id}`

**Runtime mirror**

- Code: `docker-compose`, CI workflows, ops-console
- Behavior: health endpoints, Nexus execution ledger, dashboard `/dashboard/*`
- Evidence: `aaes_exec`, `nexus_event`, `invariant_status` after CI runs

---

### Governance / Legal Steward (Dar-z)

**Runtime responsibilities**

- Validation rule definitions (law kernel, URG admission)
- Stewardship derivation logic (`identity_bridge`, DAR-Z metadata)
- Freeze criteria and cross-review protocol

**Evidence responsibilities**

- PEL mappings and dependency notes as `evidence_attached`
- Cross-review findings as `validation_decided` with explicit decision rationale
- Freeze readiness declarations as law ledger `LAW_STATUS_CHANGE` entries

**Runtime mirror**

- Code: `nova/law_kernel/`, `src/continuity/law_ledger.py`, `urg_bridge`
- Behavior: `validation_requested` → `validation_decided` before `aaes_exec`
- Evidence: `introduced_by="nova"` laws with ledger hash; `law_eval` chain

---

## Alignment principles

### 1. Every steward action leaves a runtime trace

| Steward action | Runtime artifact | Evidence event |
|----------------|------------------|----------------|
| Governance decision | Validation rule / law change | `validation_decided`, `LAW_STATUS_CHANGE` |
| Architectural decision | Schema / API change | `asset_updated`, migration evidence |
| Execution decision | Deploy / config change | `continuity_events`, deployment asset |

### 2. Runtime is the mirror of stewardship

If a rule exists, it must be visible in:

- **Code** — bridges, validators, tests
- **Runtime behavior** — spine ordering, admission gates
- **Evidence records** — continuity envelopes with hashes and foreign keys

If a freeze happens, it must be:

- **Justified by evidence** — `evidence_attached` + `validation_decided`
- **Visible in continuity** — freeze event with steward identity
- **Reflected in law_ledger** — status change with hash chain

### 3. Disagreement is evidentiary, not rhetorical

When stewards disagree, the resolution path is:

1. What evidence is missing? → add `evidence_attached` / identity snapshot
2. What runtime behavior contradicts assumptions? → run invariants, inspect `/dashboard/trace/{mission_id}`
3. Adjust rules → law kernel / validation layer
4. Re-run → `POST /dashboard/invariants/run`, `pytest tests/test_runtime_governance_invariants.py`

## Governed chain (stewardship view)

```
Identity (who) → Asset (what) → Evidence (proof) → Validation (law) → Execution (AAES) → Nexus (receipt)
```

Each hop is enforced by runtime invariants and queryable via the observability dashboard.

## Quick verification

```bash
# Run governed mission
cori mission "Stewardship alignment smoke test"

# Inspect trace
curl -s http://127.0.0.1:8000/dashboard/trace/<mission_id> | jq

# Confirm invariants
curl -s -X POST http://127.0.0.1:8000/dashboard/invariants/run | jq '.all_passed'
```

## Related

- Evidence framework: `docs/CORI_ALPHA_EVIDENCE_FRAMEWORK.md`
- Dashboard spec: `docs/CORI_ALPHA_OBSERVABILITY_DASHBOARD.md`
- Launch checklist: `docs/CORI_ALPHA_LAUNCH_CHECKLIST.md`
