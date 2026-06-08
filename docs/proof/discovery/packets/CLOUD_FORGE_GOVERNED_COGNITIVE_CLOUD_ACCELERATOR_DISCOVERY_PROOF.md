# CLOUD FORGE_ Governed Cognitive Cloud Accelerator — Proof-of-Discovery Packet

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
| Title | CLOUD FORGE_ Governed Cognitive Cloud Accelerator |
| Path | `CLOUD FORGE_ Governed Cognitive Cloud Accelerator.pdf` |
| SHA256 | `941bc02a76337ff1dcf10d4fa5cade1da8ee3c2cb0cacd8d2a1562befa6f4cb0` |
| Size | 108,069 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/CLOUD_FORGE_GOVERNED_COGNITIVE_CLOUD_ACCELERATOR_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `CLOUD FORGE_ Governed Cognitive Cloud Accelerator.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('CLOUD FORGE_ Governed Cognitive Cloud Accelerator.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
