# The Voss Binding - Unified Runtime Calculus — Proof-of-Discovery Packet

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
| Title | The Voss Binding - Unified Runtime Calculus |
| Path | `The Voss Binding - Unified Runtime Calculus.pdf` |
| SHA256 | `b3f702846d15006765875d9a0d8d321b9902e19b92ca3122745cd858a1f62757` |
| Size | 232,633 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/THE_VOSS_BINDING_UNIFIED_RUNTIME_CALCULUS_DISCOVERY_PROOF.md` |
| `claim_label` | `asserted` |
| `standing` | `2` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `The Voss Binding - Unified Runtime Calculus.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('The Voss Binding - Unified Runtime Calculus.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
