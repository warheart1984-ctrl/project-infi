# The Goblin Primer — A Runtime Field Guide to AI Governance — Proof-of-Discovery Packet

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
| Title | The Goblin Primer — A Runtime Field Guide to AI Governance |
| Path | `The Goblin Primer — A Runtime Field Guide to AI Governance.pdf` |
| SHA256 | `3511ff6f7b0cf873806762ecf3b41fdd99eb8be33aaaa00b92c84b0f9bf8d5a5` |
| Size | 170,714 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/THE_GOBLIN_PRIMER_A_RUNTIME_FIELD_GUIDE_TO_AI_GOVERNANCE_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `The Goblin Primer — A Runtime Field Guide to AI Governance.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('The Goblin Primer — A Runtime Field Guide to AI Governance.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
