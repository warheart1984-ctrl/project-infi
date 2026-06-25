# CDP-1 Governance Rules

## Rule 1 — Independence

A CDP-1 run is **invalid** if the steward participated in the original contradiction.

Enforcement: `compute_isolation_proof()` raises on participant match.

## Rule 2 — Lineage Integrity

CRR-1 and CLG-1 hashes must match canonical lineage.

Enforcement: Stage 3 of [CAA1_VALIDATION_PIPELINE.md](./CAA1_VALIDATION_PIPELINE.md).

## Rule 3 — Measurement Integrity

Governance must recompute:

- Q_pre
- Q_post
- ΔA

from raw traces.

Enforcement: `validate_cdp1_run()` metric stage.

## Rule 4 — Threshold Integrity

τA must meet governance-approved minimums.

See [TA_SPEC.md](../standards/TA_SPEC.md) and [CDP1_REPRODUCIBILITY_STANDARD.md](../standards/CDP1_REPRODUCIBILITY_STANDARD.md).

## Rule 5 — Proof Integrity

Proof bundle must match recomputed values.

Enforcement: `validate_caa1()` + schema validation.

## Rule 6 — Steward Diversity

Continuity claims require **≥ 3 independent stewards**.

See [CDP1_MULTI_STEWARD_PROTOCOL.md](../mission-006/CDP1_MULTI_STEWARD_PROTOCOL.md).

## Rule 7 — Veto Power

Any review steward may veto a CDP-1 claim with proof-based justification.

See [MULTI_STEWARD_GOVERNANCE_CHARTER.md](./MULTI_STEWARD_GOVERNANCE_CHARTER.md).

## Related

- [CDP1_CONSTITUTIONAL_SPEC.md](../continuity/CDP1_CONSTITUTIONAL_SPEC.md)
