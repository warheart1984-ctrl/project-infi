# Baseline Cognitive Profile — Jon Halstead — Proof-of-Discovery Packet

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
| Title | Baseline Cognitive Profile — Jon Halstead |
| Path | `Baseline Cognitive Profile — Jon Halstead.pdf` |
| SHA256 | `80ed3ec59ffacda0b73e8663d47be98719731d2fcc960ae40c7c5b6fa17223a5` |
| Size | 148,369 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/BASELINE_COGNITIVE_PROFILE_JON_HALSTEAD_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `Baseline Cognitive Profile — Jon Halstead.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('Baseline Cognitive Profile — Jon Halstead.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
