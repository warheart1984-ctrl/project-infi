# Chaos_Goblinus_Taxonomia_Primordialis__Field_Edition_III_2 — Proof-of-Discovery Packet

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
| Title | Chaos_Goblinus_Taxonomia_Primordialis__Field_Edition_III_2 |
| Path | `docs/fieldguide/Chaos_Goblinus_Taxonomia_Primordialis__Field_Edition_III_2.pdf` |
| SHA256 | `4b6aace0f47f2d98d0b44a80aed1ca141efec151d0cb53653bce2aec17a11cc8` |
| Size | 54,431 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/CHAOS_GOBLINUS_TAXONOMIA_PRIMORDIALIS_FIELD_EDITION_III_2_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `docs/fieldguide/Chaos_Goblinus_Taxonomia_Primordialis__Field_Edition_III_2.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('docs/fieldguide/Chaos_Goblinus_Taxonomia_Primordialis__Field_Edition_III_2.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
