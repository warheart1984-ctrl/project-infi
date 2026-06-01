# UGR Ledger Bridge Specification v1.0

Authority: [META_ARCHITECT_LAWBOOK.md](../../../META_ARCHITECT_LAWBOOK.md), [UGR_PLATFORM_CONTRACT.md](../../contracts/UGR_PLATFORM_CONTRACT.md).

Service: `ugr.ledger_bridge.v1`

## Overview

Governed transition gate between **Pattern Ledger** (causal graph / memory) and **Trust Bundle Organ** (cross-profile parity proofs). Doctrine XI: claims advance `asserted` → `proven` only through validated traversal and trust-bundle receipt.

## Bridge contract

```python
LedgerBridge.traverse(claim, lane, session_id, law_id, law_version) -> BridgeResult
LedgerBridge.query_trace(claim_id) -> list[BridgeTraceEntry]  # read-only
```

## MLCA lanes

| Lane | Traversal |
|------|-----------|
| SAFE | Always allowed when invariants pass |
| NORMAL | Default governed path |
| EXPRESS | Requires `law_clearance_token` on claim |

## Invariants (INV-BRIDGE-01..08)

| ID | Rule | Code |
|----|------|------|
| INV-BRIDGE-01 | law_id matches session | GOV-01 |
| INV-BRIDGE-02 | law_version compatible | GOV-02 |
| INV-BRIDGE-03 | sigil present, not caller-supplied only | GOV-03 |
| INV-BRIDGE-04 | source traceable to ledger node | GOV-12 |
| INV-BRIDGE-05 | no causal cycles (claim_id unique per traverse) | RNT-04 |
| INV-BRIDGE-06 | trust organ receipt before proven | GOV-08 |
| INV-BRIDGE-07 | trace appended before result returned | GOV-15 |
| INV-BRIDGE-08 | EXPRESS requires law_clearance_token | GOV-06 |

## MA-13

- **Class I:** No binding goal injection without `human_explicit` evidence link.
- **Class II:** Constraint nodes preserved in elevation payload.
- **Class III:** Read/validate/emit only — no Stage 3 apply.

## Implementation

- [`src/ugr/ledger_bridge/`](../../../src/ugr/ledger_bridge/)
- Platform read-only overlay: [`platform/ledger/ugr_bridge.py`](../../../platform/ledger/ugr_bridge.py)

## Debt

- UGR-D5 cross-machine (non-blocking)
- UGR-D7 Neo4j v2 (non-blocking)

Proof: [UGR_LEDGER_BRIDGE_V1_PROOF_BUNDLE.md](../../proof/ugr/UGR_LEDGER_BRIDGE_V1_PROOF_BUNDLE.md)
