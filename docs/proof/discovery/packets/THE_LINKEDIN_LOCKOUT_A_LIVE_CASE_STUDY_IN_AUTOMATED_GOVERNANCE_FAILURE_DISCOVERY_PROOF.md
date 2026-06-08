# The LinkedIn Lockout — A Live Case Study in Automated Governance Failure — Proof-of-Discovery Packet

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
| Title | The LinkedIn Lockout — A Live Case Study in Automated Governance Failure |
| Path | `The LinkedIn Lockout — A Live Case Study in Automated Governance Failure.pdf` |
| SHA256 | `b93cf643dbc7e6200b6dd63b7bd89b7947c25fbb63f1952944e459ce254d8c8c` |
| Size | 194,814 bytes |

## Discovery payload anchors

| Anchor | Value |
|---|---|
| `contribution_type` | `proof` |
| `proof_path` | `docs/proof/discovery/packets/THE_LINKEDIN_LOCKOUT_A_LIVE_CASE_STUDY_IN_AUTOMATED_GOVERNANCE_FAILURE_DISCOVERY_PROOF.md` |
| `claim_label` | `denied` |
| `standing` | `0` |
| `law_id` | `REPO_PROOF_LAW` |
| `discovery_pod_id` | `pod:jon-halstead` |
| `source_document_path` | `The LinkedIn Lockout — A Live Case Study in Automated Governance Failure.pdf` |

## Linked contracts

- `docs/contracts/UGR_CONTRIBUTION_DISCOVERY_CONTRACT.md`
- `docs/contracts/UGR_OPERATOR_REWARDS_CONTRACT.md`

## Verification

```bash
py -3.12 -c "from pathlib import Path; from hashlib import sha256; p=Path('The LinkedIn Lockout — A Live Case Study in Automated Governance Failure.pdf'); print(p.exists(), sha256(p.read_bytes()).hexdigest())"
```
