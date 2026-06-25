# Six Invariants — Proof-of-Discovery Packet

Claim: The historical **Six Invariants** artifact, internally resolved as the **Seven Invariants** final canonical set, is registered as governed Proof-of-Discovery evidence under UGR contribution type `proof`, attested by the first Discovery Pod.

Claim status: **proven** (artifact hash-anchored; validator pass; runtime discovery receipt recorded; final seven-invariant canonical set recorded).

## Discovery Pod

| Field | Value |
|---|---|
| Pod ID | `pod:jon-halstead` |
| Pod index | 1 (first pod) |
| Display name | Jon Halstead |
| Operator ID | `operator:jon-halstead` |
| Registry | `deploy/ugr/discovery-pods.json` |

## Source artifact

| Field | Value |
|---|---|
| Title (filename) | The Six Invariants — A Formal Framework of Cosmological and Epistemological Law |
| Internal edition title | The Seven Invariants — Complete Edition (Theoretical Framework v1.0, June 2026) |
| Path | `docs/proof/discovery/The_Six_Invariants.pdf` |
| SHA256 | `063cdc0cf1f3c2eab9fad55f998155683cb9fa5d24074d001230fccd6df4475b` |
| Size | 156,796 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/SIX_INVARIANTS_DISCOVERY_PROOF.md` |
| `claim_label` | `proven` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |

## Final canonical set

The current authority is [Seven Invariants Canonical Set](../../contracts/SEVEN_INVARIANTS_CANONICAL_SET.md).

| # | Invariant | Layer |
|---|---|---|
| 1 | Identity Preservation | Identity |
| 2 | Authority Continuity | Identity |
| 3 | Bidirectional Coherence | Transformation / Duality |
| 4 | Symmetric Constraint Surface | Transformation / Duality |
| 5 | Evidence Integrity | Governance |
| 6 | Law Surface Binding | Governance |
| 7 | The Unifier | Continuity |

The seventh invariant binds the other six into a single atomic compliance set: continuity exists only when all invariants are simultaneously satisfied.

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md` (reputation via Proof of Discovery)
- `docs/contracts/SEVEN_INVARIANTS_CANONICAL_SET.md`
- `docs/trust_bundles/SIX_INVARIANTS_DISCOVERY_PROVEN_TRUST_BUNDLE.md`

## Runtime receipt

Receipt artifact: `docs/proof/discovery/six_invariants_discovery_receipt.json`

| Field | Value |
|---|---|
| `contribution_id` | `18e95066be80e38362104c32fb47857f17ccdaebe50479515cf4c560339befcb` |
| `receipt_id` | `8949f2c2-ccf0-4cfb-a97e-8fdec9ab36ab` |
| `catalog_status` | `shadow` |

Registration parameters:

- `tenant_id`: `global`
- `operator_id`: `operator:jon-halstead`
- `aais_instance_id`: `aais-primary`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('docs/proof/discovery/The_Six_Invariants.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
py -3.12 -m pytest tests/test_ugr_contribution_discovery.py -q
```

Expected: PDF exists; SHA256 matches; contribution discovery tests pass.

## Notes

The PDF preamble describes seven paired invariants across three logical layers plus an observer interface. The repository filename follows the historical operator label **Six Invariants**; the current canonical set is **Seven Invariants**.
