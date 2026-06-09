# OTEM / Substrate Integration Map — 2026-06-07

Operator Campaign Phase 3 signoff artifact.

## Executive summary

OTEM operates on **two lanes**:

| Lane | Behavior | Default |
|------|----------|---------|
| **Proposal** | Chat produces plans + `workflow_handoff`; no direct execution | Always on when OTEM detected |
| **Execution** | Auto-enqueue → `/workflows/approvals` → approve → substrate `apply` → `ledger_record` | Level 10 (`AAIS_OTEM_CAPABILITY_LEVEL=10`) |

**Phase-2 persistence is deferred.** Substrate workflows live in-process until restart; stale approvals return **409** (by design). Contract: [OTEM_EXECUTION_SUBSTRATE.md](../contracts/OTEM_EXECUTION_SUBSTRATE.md).

### Substrate taxonomy (do not conflate)

| Name | Role | OTEM link |
|------|------|-----------|
| **OTEM Execution Substrate** | Governed approval → apply workflow | `ledger_record` = workflow stage |
| **AAIS UL Substrate** | Payload/trace envelope on status APIs | Wraps OTEM status responses |
| **Forge Substrate Evolution** | OS/distro registry + evolution ledger | **No OTEM imports** |

---

## End-to-end flow

```
POST /legacy_api/api/jarvis/chat (or session message)
  → jarvis_operator.build_otem_turn_result()
  → otem_runtime.enrich_otem_result() + workflow_handoff
  → [Level ≥ 10] maybe_enqueue_otem_execution_approval()
       → otem_execution_substrate.create_proposal()
       → workflow DB pending row (step_type: otem_execution_substrate)
       → operator_decision_ledger (pending event)
GET /workflows/approvals
POST /workflows/approvals/{id}  action=approve
  → resolve_otem_execution_approval()
       → substrate.approve() → substrate.apply() → stage=ledger_record
       → operator_decision_ledger (approve event)
```

---

## API / workflow surfaces

| Surface | Handler | Genome / gate |
|---------|---------|---------------|
| `POST /legacy_api/api/chat/sessions/{id}/message` | `src/api.py` → `jarvis_operator.build_otem_turn_result` | `otem_bounded_organ` |
| `GET/POST /workflows/approvals` | `app/main.py` | shell workflow `otem-execution-substrate` |
| `GET .../otem-bounded/status` | `src/otem_bounded_organ.py` | `otem_bounded_organ` genome |
| `GET .../otem-execution-substrate/status` | `src/jarvis_organ_status_routes.py` | `otem_execution_substrate` genome |
| Operator ledger events | `src/operator_decision_ledger.py` | `decision_kind: otem_approval` |

---

## Genome lineage

```
cognitive_bridge_organ + safety_envelope_organ + operator_profile_organ
  → otem_bounded_organ
    → otem_execution_substrate (+ coding_organs_stack parent)
```

Genomes: `governance/subsystem_genomes/otem_bounded_organ.genome.v1.json`, `otem_execution_substrate.genome.v1.json`

---

## Forge substrate matrix

| Registry ID | Ledger entry | Invariants platform | Verification |
|-------------|--------------|---------------------|--------------|
| `debian-live` | substrate.v2.registry-baseline (active) | linux | validate-substrate-invariants |
| `ubuntu-live` | substrate.v2.registry-baseline (active) | linux | validate-substrate-invariants |
| `rocky-live` | substrate.v2.rocky-live-classification (experimental) | fedora-family / fedora-liveos-layout | test_validate_substrate |
| `fedora-live` | substrate.v2.replay-adapters-non-debian | — | test_validate_substrate |
| `windows-installer` | substrate.v2.universal-windows-macos-android | windows | test_universal_substrate |
| `macos-installer` | substrate.v2.universal-windows-macos-android | macos | test_universal_substrate |
| `android-bootable` | substrate.v2.universal-windows-macos-android | android | test_universal_substrate |

Sources: `wolf-cog-os/forge/substrates/registry.json`, `.github/governance/substrate-evolution-ledger.json`, `wolf-cog-os/forge/governance/substrate-invariants.json`

---

## Test & gate inventory

| Cluster | Tests | Gate | Phase 3 fix |
|---------|-------|------|-------------|
| Evolution ledger | `test_substrate_evolution_ledger.py` | validate-substrate-evolution-ledger.py | Added `rocky-live` ledger entry |
| Universal invariants | `test_universal_substrate.py` | validate-substrate-invariants.py | Aligned linux block to v2 IDs |
| OTEM bridge | `test_otem_execution_approval_bridge.py` | otem-execution-substrate-gate | conftest substrate reset + genome boot warn |
| OTEM MVP | `test_subsystem_mvp_integration.py::test_otem_execution_substrate_workflow` | check-subsystem-mvp-integration-governance.py | contractor preview imports |
| OTEM bounded | `test_otem_bounded_organ.py` | otem-bounded-organ-gate | — |
| OTEM ceiling L20 | `test_otem_ceiling.py`, `test_otem_capability.py` | `otem-ceiling-gate`, `make otem-ceiling-invoke` | sovereign band 20; containment 16–19; `/operator/ceiling` |
| Operator ledger | `test_operator_decision_ledger.py` | — | — |

---

## Known seams / deferred debt

| Seam | Severity | Status |
|------|----------|--------|
| In-memory substrate singleton | Medium | Documented; `reset_otem_execution_substrate()` for tests |
| Stale approval after restart → 409 | Expected | Contract § Persistence phase 2 |
| Promotion rollback glob prefix collision | Fixed (Chaos Remediation) | `list_gene_backups()` |
| Checkpoint policy block on high blast-radius | Low | `OperatorDecisionCheckpointError` → 403 in FastAPI route |
| Forge vs OTEM "ledger" naming | Advisory | This map disambiguates |

---

## Live verification

```powershell
python -m aais start --data-dir ./.runtime/aais-data --preset mock --no-browser
python tools/stress/otem_approval_smoke.py
```

Smoke steps: health → OTEM status → chat OTEM turn → pending approval → approve → post-status.

---

## Closure checklist

| Check | Result |
|-------|--------|
| Integration map published | PASS |
| `rocky-live` ledger coverage | PASS (substrate.v2.rocky-live-classification) |
| Linux invariants aligned to v2 | PASS (`debian-live`, `ubuntu-live`, `debian-live-layout`, `debootstrap`) |
| OTEM pytest batch | PASS (21/21 targeted) |
| Live OTEM smoke | PASS (`tools/stress/otem_approval_smoke.py`, 0×5xx) |
| OTEM/substrate cluster 0 failures | PASS (evolution, universal, bridge, MVP, bounded, ledger) |

---

## Cross-links

- [AAIS_AGENT_WORKFLOW_CAPABILITY_MAP.md](../runtime/AAIS_AGENT_WORKFLOW_CAPABILITY_MAP.md)
- [OPERATOR_DECISION_LEDGER.md](../subsystems/platform/OPERATOR_DECISION_LEDGER.md)
- [FIRST_TIME_OPERATOR_GUIDE.md](../operations/FIRST_TIME_OPERATOR_GUIDE.md) § OTEM Level 10
- [SEAM_STRESS_RUN_2026-06-07.md](./SEAM_STRESS_RUN_2026-06-07.md)
