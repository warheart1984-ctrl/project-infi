# URG Cloud Invariants

Status: **v3.0** — super-cloud manifold + Cloud Forge rail families

Authority: `docs/contracts/URG_STACK_DOCTRINE.md`, `docs/contracts/URG_MISSION_CONTRACT.md`.

## Purpose

Lift AAIS turn-level invariant families to the **super-cloud** layer URG governs. Every mission lives inside a governed cloud manifold \(SG_{cloud}\) with frozen identity and boundary digests provable on the MissionReceipt.

## Cloud manifold

| Symbol | Definition |
|--------|------------|
| \(I_{cloud}(M)\) | SHA256(`tenant_id`, `operator_id`, `mission_id`, sorted `organ_ids`, `region_ids`, `aais_instance_id`) |
| \(B_{cloud}(M)\) | Admissible `(region, provider, rail)` tuples at mission open; digest = SHA256(canonical set) |

Stamped on ingress at mission open (`cloud_identity_hash`, `boundary_digest`, `invariant_version`).

## Invariant families

### 1. Cloud Identity

Frozen at ingress; recomputed on lifecycle transitions. Mismatch without `authorized_identity_mutation` → mission compromised (blocked).

### 2. Cloud Boundary

`organ_matcher` rejects organs outside \(B_{cloud}(M)\). Receipt organ tuples include `region_id` and `rail`.

### 3. Cloud Continuity

`valid_cloud_transition(prev, next)` on each ledger append; duplicate `step_id` rejected.

### 4. Cloud Causality

Fail-closed ledger append (`CloudCausalityFault`). Receipt build refuses when ok steps lack ledger rows.

### 5. Cloud Contract (step)

Formerly mislabeled `cloud_mutation` at step scope: domain, cost, risk ceiling per organ contract.

### 6. Cloud Mutation (governance)

URG config changes only via `mission_kind: governance_mutation` with operator allowlist / authority token. Ledger type `governance_mutation`.

### 7. Cloud Composite

Merged mission outcome respects URG law.

### 8. Cloud Execution Safety (live)

No `execution_committed` step may violate \(B_{cloud}(M)\), bypass ledger write, or emit without a valid MissionReceipt path. Enforced at the execution organ boundary in `src/ugr/invariants/execution_safety.py` via `try_commit_execution`.

### 9. Cloud Forge Rail (v3.0)

Scheduled rail must lie in runtime `B_cloud` (including federated `federation_boundary_extend` tuples). Federated steps require grant `forge_peer_rail` or `route_step`. Home vs peer rails recorded on `federation_context`.

### 10. Cloud Federation Policy (v3.0)

Peer steps require accepted bilateral grant with route capability; grant must not be revoked mid-mission.

### 11. Cloud Observed Promotion (v3.0)

`UGR_CLOUD_FORGE_OBSERVED` ledger rows do not mutate `tenants.json`. `cloud_forge_submit_promotion` on mission ingress requires `URG_GOVERNANCE_APPLY=1` and governance `cloud_forge_profile_update`.

## Implementation

| Module | Path |
|--------|------|
| Manifold | `src/ugr/invariants/cloud_manifold.py` |
| Checks | `src/ugr/invariants/cloud_invariants.py` |
| Mission shim | `src/ugr/mission/cloud_invariants.py` |
| Governance | `src/ugr/mission/governance_mission.py` |
| Execution safety | `src/ugr/invariants/execution_safety.py` |
| Execution policy | `src/ugr/mission/execution_policy.py`, `step_execution.py` |
| Runtime | `src/ugr/mission/mission_runtime.py` |

## API

- `POST /api/ugr/mission/run` — step missions
- `POST /api/ugr/mission/governance` — governance mutations

## Verification

```bash
py -3.12 -m pytest tests/test_ugr_cloud_invariants.py tests/test_ugr_mission_demo.py tests/test_ugr_execution_policy.py -q
py -3.12 wolf-cog-os/scripts/validate-ugr-mission-manifest.py
```
