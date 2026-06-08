# Anchor_Connectome_Framework_Grant_Proposal_v2_1 — Proof-of-Discovery Packet

Claim: Source PDF registered as governed Proof-of-Discovery evidence under UGR contribution type `proof`, attested by Discovery Pod **Jon Halstead**.

Claim status: **denied** (standing 0; artifact hash-anchored; validator pass).

## Discovery Pod

| Field | Value |
|---|---|
| Pod ID | `pod:jon-halstead` |
| Display name | Jon Halstead |
| Operator ID | `operator:jon-halstead` |

## Source artifact

| Field | Value |
|---|---|
| Title | Anchor_Connectome_Framework_Grant_Proposal_v2_1 |
| Path | `Anchor_Connectome_Framework_Grant_Proposal_v2_1.pdf` |
| SHA256 | `3f1272ebea5f0fdd73251cd1f41862d6a898d0454394009c63e0989fae1e852a` |
| Size | 69,669 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/ANCHOR_CONNECTOME_FRAMEWORK_GRANT_PROPOSAL_V2_1_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `Anchor_Connectome_Framework_Grant_Proposal_v2_1.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('Anchor_Connectome_Framework_Grant_Proposal_v2_1.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
