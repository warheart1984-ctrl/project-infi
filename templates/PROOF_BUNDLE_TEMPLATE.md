# Proof Bundle Template

Use this template for every fix/test/release claim. Completed bundles are required by `REPO_PROOF_LAW.md` under `META_ARCHITECT_LAWBOOK.md`.

## 1) Incident / Issue ID

- ID:
- Title:
- Scope:
- Severity:
- Linked tracker/docs:

## 2) Hypothesis And Root Cause

- Initial hypothesis:
- Confirmed root cause:
- Why this root cause is credible:
- Conditions required to trigger:

## 3) Reproduction Steps

- Environment profile(s):
- Preconditions:
- Steps:
  1.
  2.
  3.
- Expected failure signal:
- Actual failure signal:

## 4) Fix Details (What / Why / How)

- What changed:
- Why this approach:
- How it addresses root cause:
- Files/artifacts changed:
- Risks and mitigations:

## 5) Verification Evidence

### Commands

```text
# paste exact commands here
```

### Outputs

```text
# paste key command outputs, exit codes, and relevant log lines
```

### Artifact Hashes

```text
# e.g., sha256sum outputs and verification results
```

### Screenshot / Video References

- Reference 1:
- Reference 2:

## 6) Hardware Matrix

| Machine | Role (Old/New) | Firmware (BIOS/UEFI) | Secure Boot | Test Set | Outcome | Evidence Ref |
|---|---|---|---|---|---|---|
| machine-a | old | BIOS | Off | | | |
| machine-b | new | UEFI | Off | | | |

Notes:
- Add rows as needed.
- A single-machine pass is not acceptance.

## 7) Time / Author / Sign-Off

- Start time (UTC):
- End time (UTC):
- Author:
- Reviewer:
- Sign-off decision:
  - [ ] Asserted (insufficient proof)
  - [ ] Proven (evidence complete)
  - [ ] Rejected (disproven or incomplete)
- Approval timestamp:
