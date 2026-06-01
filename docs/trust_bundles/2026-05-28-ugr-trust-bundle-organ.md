# Trust Bundle: UGR Trust Bundle Organ

```text
claim_label: proven
why_short: |
  Trust bundle organ runs mesh parity, causal rebuild, LLM execution smoke, and manifest gate.
  machine-a and machine-b isolated profiles produce matching payload hashes for deterministic scenarios.
  Cross-physical-machine OS matrix remains tracked as UGR-D5 asserted debt.
proof_links:
  - docs/proof/ugr/UGR_TRUST_BUNDLE_ORGAN_PROOF.md
  - docs/contracts/UGR_TRUST_BUNDLE_ORGAN_CONTRACT.md
  - tests/test_ugr_trust_bundle_organ.py
none_yet: false
override_command: make ugr-trust-bundle-gate
override_breaks_blueprint: false
debt_ticket_ref: UGR-D5
created_at_utc: 2026-05-28T18:00:00Z
updated_at_utc: 2026-05-28T18:00:00Z
author: cursor-agent
context: ugr-trust-bundle-organ-v1
```

## Verification

```bash
make ugr-trust-bundle-gate
python tools/proof/run_ugr_trust_bundle.py --mode fail
```

## Open debt

- **UGR-D5**: Attach CI matrix proof from ubuntu + windows runners to upgrade cross-machine claim to proven.
