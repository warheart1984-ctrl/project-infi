# Invariant Calculus Explained for Engineers (1) — Proof-of-Discovery Packet

Claim: Source PDF registered as governed Proof-of-Discovery evidence under UGR contribution type `proof`, attested by Discovery Pod **Jon Halstead**.

Claim status: **hypothetical** (standing 1; artifact hash-anchored; validator pass).

## Discovery Pod

| Field | Value |
|---|---|
| Pod ID | `pod:jon-halstead` |
| Display name | Jon Halstead |
| Operator ID | `operator:jon-halstead` |

## Source artifact

| Field | Value |
|---|---|
| Title | Invariant Calculus Explained for Engineers (1) |
| Path | `Invariant Calculus Explained for Engineers (1).pdf` |
| SHA256 | `9657f87c89b41b6bbd85da3b6f2b3165fa1b0a5d4443c4788efd350bf76651b3` |
| Size | 384,016 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/INVARIANT_CALCULUS_EXPLAINED_FOR_ENGINEERS_1_DISCOVERY_PROOF.md` |
| `claim_label` | `hypothetical` |
| `standing` | `1` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `Invariant Calculus Explained for Engineers (1).pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('Invariant Calculus Explained for Engineers (1).pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
