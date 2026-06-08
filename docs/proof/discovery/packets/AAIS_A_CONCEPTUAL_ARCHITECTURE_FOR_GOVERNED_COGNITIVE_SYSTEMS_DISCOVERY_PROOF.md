# AAIS - A Conceptual Architecture for Governed Cognitive Systems — Proof-of-Discovery Packet

Claim: Source PDF registered as governed Proof-of-Discovery evidence under UGR contribution type `proof`, attested by Discovery Pod **Jon Halstead**.

Claim status: **asserted** (artifact hash-anchored; validator pass).

## Discovery Pod

| Field | Value |
|---|---|
| Pod ID | `pod:jon-halstead` |
| Display name | Jon Halstead |
| Operator ID | `operator:jon-halstead` |

## Source artifact

| Field | Value |
|---|---|
| Title | AAIS - A Conceptual Architecture for Governed Cognitive Systems |
| Path | `AAIS - A Conceptual Architecture for Governed Cognitive Systems.pdf` |
| SHA256 | `f79dd00b8032efcbee35c1cc4273588e378c63a323ef7a5ac03225893324a495` |
| Size | 335,240 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/AAIS_A_CONCEPTUAL_ARCHITECTURE_FOR_GOVERNED_COGNITIVE_SYSTEMS_DISCOVERY_PROOF.md` |
| `claim_label` | `asserted` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `AAIS - A Conceptual Architecture for Governed Cognitive Systems.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('AAIS - A Conceptual Architecture for Governed Cognitive Systems.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
