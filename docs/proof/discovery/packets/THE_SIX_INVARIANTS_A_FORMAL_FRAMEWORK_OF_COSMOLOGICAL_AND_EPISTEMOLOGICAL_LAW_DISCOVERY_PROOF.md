# The Six Invariants — A Formal Framework of Cosmological and Epistemological Law — Proof-of-Discovery Packet

Claim: Source PDF registered as governed Proof-of-Discovery evidence under UGR contribution type `proof`, attested by Discovery Pod **Jon Halstead**.

Claim status: **proven** (standing 3; artifact hash-anchored; validator pass; final seven-invariant canonical set recorded).

## Discovery Pod

| Field | Value |
|---|---|
| Pod ID | `pod:jon-halstead` |
| Display name | Jon Halstead |
| Operator ID | `operator:jon-halstead` |

## Source artifact

| Field | Value |
|---|---|
| Title | The Six Invariants — A Formal Framework of Cosmological and Epistemological Law |
| Path | `The Six Invariants — A Formal Framework of Cosmological and Epistemological Law.pdf` |
| SHA256 | `063cdc0cf1f3c2eab9fad55f998155683cb9fa5d24074d001230fccd6df4475b` |
| Size | 156,796 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/THE_SIX_INVARIANTS_A_FORMAL_FRAMEWORK_OF_COSMOLOGICAL_AND_EPISTEMOLOGICAL_LAW_DISCOVERY_PROOF.md` |
| `claim_label` | `proven` |
| `standing` | `3` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `The Six Invariants — A Formal Framework of Cosmological and Epistemological Law.pdf` |

## Final canonical set

The historical Six Invariants artifact is canonically resolved to the Seven Invariants final set:

1. Identity Preservation
2. Authority Continuity
3. Bidirectional Coherence
4. Symmetric Constraint Surface
5. Evidence Integrity
6. Law Surface Binding
7. The Unifier

Canonical contract: `docs/contracts/SEVEN_INVARIANTS_CANONICAL_SET.md`

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`
- `docs/contracts/SEVEN_INVARIANTS_CANONICAL_SET.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('The Six Invariants — A Formal Framework of Cosmological and Epistemological Law.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
