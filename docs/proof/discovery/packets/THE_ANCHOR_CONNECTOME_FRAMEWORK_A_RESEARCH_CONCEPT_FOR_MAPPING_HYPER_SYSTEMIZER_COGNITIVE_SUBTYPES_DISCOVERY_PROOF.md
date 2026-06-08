# The Anchor-Connectome Framework — A Research Concept for Mapping Hyper-Systemizer Cognitive Subtypes — Proof-of-Discovery Packet

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
| Title | The Anchor-Connectome Framework — A Research Concept for Mapping Hyper-Systemizer Cognitive Subtypes |
| Path | `The Anchor-Connectome Framework — A Research Concept for Mapping Hyper-Systemizer Cognitive Subtypes.pdf` |
| SHA256 | `7d54748629bdbb244695b27aade9ac87a35698f94da32783fe3d6f0f7ca0db40` |
| Size | 251,450 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/THE_ANCHOR_CONNECTOME_FRAMEWORK_A_RESEARCH_CONCEPT_FOR_MAPPING_HYPER_SYSTEMIZER_COGNITIVE_SUBTYPES_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `The Anchor-Connectome Framework — A Research Concept for Mapping Hyper-Systemizer Cognitive Subtypes.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('The Anchor-Connectome Framework — A Research Concept for Mapping Hyper-Systemizer Cognitive Subtypes.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
