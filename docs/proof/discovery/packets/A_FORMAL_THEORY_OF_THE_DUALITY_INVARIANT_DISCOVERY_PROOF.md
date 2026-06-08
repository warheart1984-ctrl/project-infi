# A Formal Theory of the Duality Invariant — Proof-of-Discovery Packet

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
| Title | A Formal Theory of the Duality Invariant |
| Path | `A Formal Theory of the Duality Invariant.pdf` |
| SHA256 | `cfa48264bd0226117caf8dea623deacc8338770e15b631ccaa78c1046d05968b` |
| Size | 202,942 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/A_FORMAL_THEORY_OF_THE_DUALITY_INVARIANT_DISCOVERY_PROOF.md` |
| `claim_label` | `hypothetical` |
| `standing` | `1` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `A Formal Theory of the Duality Invariant.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('A Formal Theory of the Duality Invariant.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
