# The Goblin Engineer's Guide to the Cognitive Universe — Proof-of-Discovery Packet

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
| Title | The Goblin Engineer's Guide to the Cognitive Universe |
| Path | `The Goblin Engineer's Guide to the Cognitive Universe.pdf` |
| SHA256 | `d059c553430fd2c7c65d442430f4223598fab47d10a1e429917b2db0f3b953bc` |
| Size | 371,338 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/THE_GOBLIN_ENGINEER_S_GUIDE_TO_THE_COGNITIVE_UNIVERSE_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `The Goblin Engineer's Guide to the Cognitive Universe.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('The Goblin Engineer's Guide to the Cognitive Universe.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
