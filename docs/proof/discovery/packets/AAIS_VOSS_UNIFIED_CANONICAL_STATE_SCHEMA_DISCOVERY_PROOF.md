# AAIS–Voss Unified Canonical State Schema — Proof-of-Discovery Packet

Claim: Source PDF registered as governed Proof-of-Discovery evidence under UGR contribution type `proof`, attested by Discovery Pod **Jon Halstead**.

Claim status: **asserted** (standing 2; artifact hash-anchored; validator pass).

## Discovery Pod

| Field | Value |
|---|---|
| Pod ID | `pod:jon-halstead` |
| Display name | Jon Halstead |
| Operator ID | `operator:jon-halstead` |

## Source artifact

| Field | Value |
|---|---|
| Title | AAIS–Voss Unified Canonical State Schema |
| Path | `AAIS–Voss Unified Canonical State Schema.pdf` |
| SHA256 | `9699c51edd5100b83cb2fa38fe759f6f18355d8a7806437192b8e18da6a8b6ff` |
| Size | 588,418 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/AAIS_VOSS_UNIFIED_CANONICAL_STATE_SCHEMA_DISCOVERY_PROOF.md` |
| `claim_label` | `asserted` |
| `standing` | `2` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `AAIS–Voss Unified Canonical State Schema.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('AAIS–Voss Unified Canonical State Schema.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
