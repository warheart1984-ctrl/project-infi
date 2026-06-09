# Trust Bundle — Operator Document Corpus Proof-of-Discovery

```text
claim_label: asserted
why_short: |
  Thirty operator PDFs under project-infi (repo root and docs/fieldguide) are hash-anchored
  with governed proof packets in docs/proof/discovery/packets/, registered via UGR
  contribution discovery under Discovery Pod Jon Halstead. Six Invariants retains a
  separate canonical proven registration (SIX_INVARIANTS_DISCOVERY_PROOF.md).
proof_links:
  - docs/proof/discovery/DISCOVERY_DOCUMENT_MANIFEST.json
  - docs/proof/discovery/packets/
  - docs/proof/discovery/receipts/
  - docs/proof/discovery/SIX_INVARIANTS_DISCOVERY_PROOF.md
  - deploy/ugr/discovery-pods.json
none_yet: false
override_command: py -3.12 tools/governance/register_discovery_documents.py --dry-run
override_breaks_blueprint: false
debt_ticket_ref: none
created_at_utc: 2026-06-08T00:00:00Z
updated_at_utc: 2026-06-08T00:00:00Z
author: Jon Halstead
context: Bulk operator document corpus registration for Proof-of-Discovery
```
