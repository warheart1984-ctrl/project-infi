# PROOF-2.5: Enforcement Under Partial Trust

## Claim
CEN maintains constitutional integrity when actors, payloads, or authority tokens are partially trusted or adversarial.

## Implementation
Authority tokens bind type, scope, transition ID, expiry, and placeholder signature. Invalid, expired, out-of-scope, mismatched, or replayed tokens produce `token_refusal` receipts.

## Evidence
- Authority token API in `@aaes-os/constitutional-enforcement-node`
- Sovereignty ledger entries in `@aaes-os/sovereignty-ledger`
- Partial trust scenarios in `@aaes-os/omega-stress-harness`
