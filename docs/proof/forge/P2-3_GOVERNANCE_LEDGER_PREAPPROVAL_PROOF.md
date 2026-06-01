# P2-3 Governance Ledger Pre-Approval Proof

Status: **cutover approved and activated** for `P2-3 Tighten drift policy from warn to fail`.

## Scope

- Milestone: `P2-3`
- Authoritative order: `META_ARCHITECT_LAWBOOK.md` > `docs/forge-build-program.md` > `docs/forge-backlog.md` > `docs/forge-risk-register.md` > `docs/forge-iso-design.md`
- Purpose: record pre-approval evidence and post-approval cutover decision for governance ledger default enforcement.

## Claim Ledger

| Claim ID | Claim | Label | Why |
|---|---|---|---|
| C1 | Forge workflow wiring supports explicit governance ledger mode selection (`warn` or `fail`) while default remains `warn`. | proven (historical) | Pre-cutover wiring constrained dispatch input to `warn`/`fail` with `warn` default. |
| C2 | Governance ledger validator passes in both modes on this working tree. | proven | Dual-mode governance validation commands pass with zero warnings/errors in both `warn` and `fail` modes. |
| C3 | P2-3 default fail cutover is ready for activation. | **proven (post-approval)** | Meta Architect approval recorded below; workflow defaults changed to `fail`. |
| C4 | Workflow default governance enforcement is now `fail`. | proven | All Forge-relevant workflows now default `governance_ledger_mode` to `fail` and env fallback uses `fail`. |

## Meta Architect Decision

| Field | Value |
|---|---|
| Decision | **APPROVED** — activate default governance ledger enforcement mode `fail` |
| Authority | Meta Architect (operator directive in session) |
| Decision date | 2026-05-27 |
| Scope | `.github/workflows/cogos-ci-public.yml`, `.github/workflows/cogos-ci-selfhosted.yml`, `.github/workflows/cogos-rc.yml`, `.github/workflows/cogos-release.yml` |
| Rollback | Dispatch input may still select `warn` explicitly for temporary audit-only runs |

## Verification Commands

```text
python3 .github/scripts/validate-governance-ledger.py --mode warn --summary-only
python3 .github/scripts/validate-governance-ledger.py --mode fail
python3 .github/scripts/validate-documentation-baseline.py
```

## Post-Cutover Verification Outputs (local)

```text
Governance ledger check: commands=21, warnings=0, errors=0, mode=fail
Repo safety check: surfaces=4, files=55, violations=0
```

## Required Approval Packet Criteria Tracking

| Criterion | Status | Evidence |
|---|---|---|
| Dual-mode governance validator success (`warn` + `fail`) | Proven | Local validator outputs (`warnings=0`, `errors=0` in both modes) |
| No unresolved Forge governance debt for command-surface drift in tracked debt register | Proven | `validate-documentation-baseline.py` + `docs/forge-risk-register.md` |
| At least one successful dry-run per relevant Forge workflow with explicit mode selection | Pending (CI run) | Requires next workflow run artifact links after merge |
| Meta Architect decision recorded and linked before default cutover | **Proven** | This packet decision table + backlog P2-3 status update |

## Remaining Follow-Up

- Capture first post-cutover workflow-run evidence links in this packet after CI executes with default `fail` mode.
