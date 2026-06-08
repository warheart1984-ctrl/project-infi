# Architectural Hyper-Systemizer — Formal Specification v2.0 — Proof-of-Discovery Packet

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
| Title | Architectural Hyper-Systemizer — Formal Specification v2.0 |
| Path | `Architectural Hyper-Systemizer — Formal Specification v2.0.pdf` |
| SHA256 | `7291408247140e790945773d9f6d55d4b91caed85fc2f0e1a77ba28f8f7f2672` |
| Size | 163,798 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/ARCHITECTURAL_HYPER_SYSTEMIZER_FORMAL_SPECIFICATION_V2_0_DISCOVERY_PROOF.md` |
| `claim_label` | `asserted` |
| `standing` | `2` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `Architectural Hyper-Systemizer — Formal Specification v2.0.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('Architectural Hyper-Systemizer — Formal Specification v2.0.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
