# UGR Contribution Discovery Contract (v1.1)

Governed Proof-of-Discovery for six contribution types under URG cloud law.

## Contribution types

| Type | Payload anchors |
|------|-----------------|
| `subsystem` | `role`, `io_shape`, `rail_class`, `risk_ceiling`, `tenant_class` |
| `workflow` | `workflow_id`, `run_id`, `step_count` |
| `organ` | `organ_id`, `governance_mission_id` |
| `proof` | `proof_path` or `gene`, `claim_label` |
| `invariant` | `mission_id`, `invariant_digest`, `all_passed` |
| `capability` | `trace_id`, `module`, `action`, `ok` |
| `substrate` | `claim_id` or `surface`, `substrate_id` |

## Canonical ID

`contribution_id = SHA256(contribution_type + stable_json(normalized_payload))`

## API

| Method | Path |
|--------|------|
| POST | `/api/ugr/discover/contribution` |
| POST | `/api/ugr/discover/subsystem` (legacy alias) |
| GET | `/api/ugr/discover/contribution/<id>?tenant_id=` |

## Implementation

- `src/ugr/discovery/contribution_discovery.py`
- `src/ugr/discovery/validators/`
- `src/ugr/discovery/proven_contribution.py` — proven detection for auto-reward
- `src/ugr/discovery/discovery_pod_ledger.py` — `pod_proven` events and registry totals
- `src/ugr/discovery/pod_admission.py` — automatic pod worthiness evaluation

## Discovery Pod auto-admission

New pods are **not** registered on every discovery. After resolving operator/pod context, the pipeline evaluates **`deploy/ugr/discovery-pod-admission.json`** (override: `UGR_DISCOVERY_POD_ADMISSION_POLICY_PATH`):

| Signal | Effect |
|---|---|
| `discovery_pod_id` / `pod_display_name` in payload | Admit when `explicit_pod_requires_receipt` is false (default); otherwise require verified signed receipt |
| `claim_label: proven` on signed receipt | Admit |
| Proven `capability` / `substrate` when `admit_deferred_types_when_proven` is true | Admit (`deferred_type_proven:*`) even if `admit_on_proven` is false |
| Contribution type in `admit_contribution_types` + verified receipt + invariant passes | Admit |
| Types in `defer_types_until_proven` (e.g. capability, substrate) without proven | Skip registration |
| Denied operator slugs (`system`, `anonymous`, …) | Skip |

When admission fails, `discovery_pod_ledger.skipped` is true and `skip_reason` explains why (no `pod_registered` row). Existing pods still receive `pod_discovered` on later eligible discoveries.

Admission outcomes increment in-process counters (`src/ugr/discovery/pod_admission_metrics.py`): `admit_total`, `skip_total`, and `admit:*` / `skip:*` by reason (e.g. `skip:insufficient_invariant_passes`). Optional snapshot: `write_metrics_snapshot(path)`.

Both discovery routes run the same admission path:

- **Unified contribution discovery** (`ContributionDiscoveryService.discover` without legacy `spec`-only shortcut)
- **Subsystem-only discovery** (`SubsystemDiscoveryService.discover` when `contribution_type=subsystem` and `spec` is present)

Override the minimum invariant pass threshold with `UGR_POD_MIN_INVARIANT_PASS_COUNT` (policy default: `min_invariant_pass_count` in `discovery-pod-admission.json`, currently `1`).

Require a verified receipt for explicit pod fields with policy `explicit_pod_requires_receipt: true` or env `UGR_POD_EXPLICIT_REQUIRES_RECEIPT=1`.

Disable auto-admission entirely with `UGR_POD_AUTO_ADMIT=0`. Manual CLI registration remains available.

## Governance arc pod reward multiplier

Contributions tagged **High / Beyond the Body** (`governance_arc: high`, anatomical layers 14–16, `beyond-body` batch ids) or **Civilizational** (`governance_arc: civilizational`, layers 17+, `civilizational-arc` batches) receive a **10×** multiplier on reputation and rail credits (policy: `pod_arc_multipliers` in `deploy/ugr/reward-policy.json` and `discovery-pod-admission.json`).

Env overrides: `UGR_POD_ARC_MULTIPLIER_HIGH`, `UGR_POD_ARC_MULTIPLIER_CIVILIZATIONAL`, or global `UGR_POD_ARC_MULTIPLIER`.

Reward deltas include `governance_arc_tier` and `pod_reward_multiplier`. Pod ledger events and registry entries expose the highest arc tier and multiplier observed per pod.

## Library Standing (v3)

Every contribution and discovery document carries a **Standing** tier that governs library admission, authority, and rewards.

| Standing | `claim_label` | In library | Authority | Rewards |
|----------|---------------|------------|-----------|---------|
| 0 | `denied` | No (manifest audit only) | None | None |
| 1 | `hypothetical` | Yes | Ideas/theory | Minimal (0.25× reputation, 0 credits) |
| 2 | `asserted` | Yes | Structured, unverified | Base policy amounts |
| 3 | `proven` | Yes | Verified | Base + promotion bonus; `force_persist` enabled |

Resolution order (first match wins): **denied** → **proven** (requires verification signals) → **hypothetical** → **asserted**.

**Proven (3)** requires `receipt_verified` plus at least one of: `ci_structural_test`, `subsystem_genome_gate`, `workflow_otem_gate`, or non-empty `verification.artifacts[]`. Pattern/regex promotion alone caps at **asserted (2)**.

Manifest fields: `standing`, `claim_label`, `library_admitted`, `promotion_rule`, `verification`. Standing 0 skips `discover()` and withdraws from the discovery store on reconcile.

Policy: `deploy/ugr/discovery-proof-promotion.json` (v3). Rewards: `deploy/ugr/reward-policy.json` `standing` block.

Subsystem, workflow, and organ registrations default to **standing 2** at ingest.

## Proven contributions and operator rewards

When a discovery receipt has **Standing 3** / `claim_label: proven` (with verification signals for documents), the discovery pipeline:

1. **Issues operator rewards** using the inline signed receipt (no store re-resolution).
2. **Persists balances** even when `UGR_REWARDS_SHADOW_ONLY=1`, unless `UGR_REWARDS_PROVEN_PERSIST=0`.
3. **Upgrades the pod ledger** with a `pod_proven` event and updates registry fields: `proven_count`, `total_reputation_awarded`, `last_proven_at_utc`.

Idempotent rediscovery of a proven contribution still attempts reward issuance once (subsequent calls return `idempotent` if already issued).

Discovery responses include `operator_rewards` and `discovery_pod_ledger.pod_proven` when applicable.

## Epistemic state layer (v1)

URG adds a canonical **3-state epistemic layer** on top of 4-band Standing. Standing remains authoritative for rewards and library admission; epistemic state governs operator promotion and chat/workbench injection.

| `epistemic_state` | Maps from Standing / signals |
|-------------------|------------------------------|
| `rejected` | `denied`, `claim_label: rejected`, `rejection_source`, falsified fingerprint |
| `pending` | `hypothetical`, `asserted` |
| `proven` | `proven` with verification signals |

Schema: `schemas/epistemic_state.v1.json`. Implementation: `src/ugr/discovery/standing.py`, contract: `docs/contracts/URG_EPISTEMIC_STATE_CONTRACT.md`.

Rejected claims are recorded in `src/rls/falsity_registry.py` with `epistemic_state: rejected` and cannot silently re-enter via promotion (`is_resurrection_blocked`).

## Operator knowledge bridge

Proven URG receipts may be promoted into governed operator knowledge:

- Module: `src/urg_operator_knowledge_bridge.py`
- Idempotency ledger: `.runtime/urg_operator_promotions.jsonl`
- Memory writes: `category: urg_proven`, `source: urg_library`, `truth_status: canonical`
- ODL events: `urg_knowledge_promotion` via `src/operator_decision_ledger.py`
- Knowledge authority source: `urg_library` in `src/knowledge_authority.py`
- Chat/workbench injection: `urg_library_context` prompt block (parity with `live_research`)

Automatic promotion runs when `discovery_pod_ledger.record_proven()` fires (`pod_proven` path). Manual promotion:

| Method | Path |
|--------|------|
| POST | `/api/operator/knowledge/promote-from-urg` |

Body: `{ "contribution_id", "operator_id", "tenant_id?" }`. Loads receipt from `ContributionDiscoveryStore` and calls `promote_from_receipt()`.
