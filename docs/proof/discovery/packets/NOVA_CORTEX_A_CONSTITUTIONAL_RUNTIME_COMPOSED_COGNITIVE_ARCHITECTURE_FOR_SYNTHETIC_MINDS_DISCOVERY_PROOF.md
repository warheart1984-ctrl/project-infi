# Nova Cortex_ A Constitutional, Runtime‑Composed Cognitive Architecture for Synthetic Minds — Proof-of-Discovery Packet

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
| Title | Nova Cortex_ A Constitutional, Runtime‑Composed Cognitive Architecture for Synthetic Minds |
| Path | `Nova Cortex_ A Constitutional, Runtime‑Composed Cognitive Architecture for Synthetic Minds.pdf` |
| SHA256 | `0ba57c77ccb59bdcf9a6d383f5d0d58ca9d5f100bc0825bcf6e1ef66b7ea6d54` |
| Size | 114,673 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/NOVA_CORTEX_A_CONSTITUTIONAL_RUNTIME_COMPOSED_COGNITIVE_ARCHITECTURE_FOR_SYNTHETIC_MINDS_DISCOVERY_PROOF.md` |
| `claim_label` | `asserted` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `Nova Cortex_ A Constitutional, Runtime‑Composed Cognitive Architecture for Synthetic Minds.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('Nova Cortex_ A Constitutional, Runtime‑Composed Cognitive Architecture for Synthetic Minds.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
