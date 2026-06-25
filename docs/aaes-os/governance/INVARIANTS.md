# AAES-OS Constitutional Invariants

Frozen invariant set for v1.0. See also [Constitution](CONSTITUTION.md).

## Meta-invariants

| ID | Name | Summary |
|----|------|---------|
| **K-∞** | Meta-invariant | Governs all invariants; no invariant may contradict the constitutional object model |
| **KΩ** | Reconstruction | All states reconstructable from receipts and evidence |

## Operational invariants (K0–K15)

| ID | Summary |
|----|---------|
| K0 | No empty governed runs |
| K1 | Every span declares parent linkage |
| K2 | No finalize without result span |
| K3 | Receipts are content-addressed and immutable |
| K4 | No nondeterministic branches in CRK-1 |
| K5 | No side-effects outside receipt ledger |
| K6 | Constitutional boot must pass before execution |
| K7 | Proof gate validates every transition |
| K8 | Capability gate enforces authorized actions |
| K9 | Drift observations are journaled |
| K10 | CTS must pass for release candidates |
| K11 | CDP-1 thresholds are published and fixed |
| K12 | CEP experiments are replay-deterministic |
| K13 | No hidden model state in governed path |
| K14 | Challenge-response archive is public |
| K15 | Amendments follow evidence-driven process |

## Adding invariants

Forbidden in v1.0 without Governance Council unanimous consent. See [Tutorial: Writing an Invariant](../dev/TUTORIAL_04_WRITING_AN_INVARIANT.md).
