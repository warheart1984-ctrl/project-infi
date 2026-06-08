# ProjectInfinity_UL_Documentation (1) — Proof-of-Discovery Packet

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
| Title | ProjectInfinity_UL_Documentation (1) |
| Path | `ProjectInfinity_UL_Documentation (1).pdf` |
| SHA256 | `eba19604bbf5648f1f6779e8665efc92ca7fb0074e8b0295ceca63dfb438e5a3` |
| Size | 37,783 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/PROJECTINFINITY_UL_DOCUMENTATION_1_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `ProjectInfinity_UL_Documentation (1).pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('ProjectInfinity_UL_Documentation (1).pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
