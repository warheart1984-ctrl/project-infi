# The Global Policy Genome — Toward a Computational Framework for Comparative Governance (1) — Proof-of-Discovery Packet

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
| Title | The Global Policy Genome — Toward a Computational Framework for Comparative Governance (1) |
| Path | `The Global Policy Genome — Toward a Computational Framework for Comparative Governance (1).pdf` |
| SHA256 | `9c0473043818fbe60c76298ec5f996c501d785b6491cac2b1fa1935b46d2168e` |
| Size | 345,722 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/THE_GLOBAL_POLICY_GENOME_TOWARD_A_COMPUTATIONAL_FRAMEWORK_FOR_COMPARATIVE_GOVERNANCE_1_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `The Global Policy Genome — Toward a Computational Framework for Comparative Governance (1).pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('The Global Policy Genome — Toward a Computational Framework for Comparative Governance (1).pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
