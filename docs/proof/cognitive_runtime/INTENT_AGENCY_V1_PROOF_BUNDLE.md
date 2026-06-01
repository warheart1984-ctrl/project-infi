# Nova Cortex v3.0 — Intent Core agency proof gate (items 1–5 integration).

**Claim status (single-machine):** **proven** via pytest + `check-nova-intent-agency.py`  
**Cross-machine wolf reboot agency survival:** **debt**

## Scope

1. Deliberation + Planning consume Intent (`intent_alignment`, chain scoring)
2. Commitment conflict + deferral (`in_tension`, `deferred`, `story_intent`)
3. Unified closure (`unified_closure` across arc / execution / intent)
4. Claim posture (`claim_posture` per commitment, `continuity_claim_posture`)
5. Session-reset evidence fixture (3-turn harness + survival metrics)

## Verification (one-click)

```bash
pytest tests/test_intent_core.py tests/test_intent_store.py tests/test_intent_agency_evidence.py -q
python .github/scripts/check-nova-intent-agency.py
python .github/scripts/check-nova-cortex-governance.py
```

## Evidence table

| # | Claim | Status | Artifact |
|---|-------|--------|----------|
| 1 | Deliberation records `intent_influence` and weights safe path under safety pull | **proven** | `test_deliberation_weights_safe_path_under_safety_pull` |
| 2 | Planning honors active commitments in steps/chains | **proven** | `test_planning_prefers_commitment_chain` |
| 3 | Opposing commitments surface `commitment_conflicts` | **proven** | `test_commitment_conflict_detected` |
| 4 | Unified closure spans arc + intent layers | **proven** | `test_unified_closure_event`, narrative `turn_delta.unified_closure` |
| 5 | Session reset retains commitments; claim posture covered | **proven** | `test_three_turn_session_reset_fixture`, CI fixture |
| 6 | Wolf metal reboot same `active_commitments` | **debt** | Cross-machine proof bundle TBD |

## Why

Intent Core v0.1 stored agency; v0.2 makes **why constrain choice** (lobe consult), makes **conflicts visible**, records **closure**, labels **claim posture**, and proves **commitment survival** across simulated session boundaries.
