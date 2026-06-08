# SEA-FORGE_ An Industrial-Scale Seaweed‑Fed Cultured Meat and 3D‑Printed Food Fabrication Pipeline — Proof-of-Discovery Packet

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
| Title | SEA-FORGE_ An Industrial-Scale Seaweed‑Fed Cultured Meat and 3D‑Printed Food Fabrication Pipeline |
| Path | `SEA-FORGE_ An Industrial-Scale Seaweed‑Fed Cultured Meat and 3D‑Printed Food Fabrication Pipeline.pdf` |
| SHA256 | `28ee63978b056f67ea4260d1d66ac2639e5dd35898b8b00ee96c3e31600c0f21` |
| Size | 136,325 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/SEA_FORGE_AN_INDUSTRIAL_SCALE_SEAWEED_FED_CULTURED_MEAT_AND_3D_PRINTED_FOOD_FABRICATION_PIPELINE_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `SEA-FORGE_ An Industrial-Scale Seaweed‑Fed Cultured Meat and 3D‑Printed Food Fabrication Pipeline.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('SEA-FORGE_ An Industrial-Scale Seaweed‑Fed Cultured Meat and 3D‑Printed Food Fabrication Pipeline.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
