# Help Wanted Hub — Stage 18 Co-Builders

Project Infinity 1 is at **Civilizational Stage 18**. This page is the in-repo index for bite-sized contribution entry points.

## Start here

1. **[Stage 18 — Call for Co-Builders](https://github.com/warheart1984-ctrl/Project-Infinity1/discussions/9)** — pinned discussion (Announcements). Comment *"I'd like to take #N"* on a ticket below.
2. **[How to join in 10 minutes](../README.md#how-to-join-in-10-minutes)** — clone, mock mode, health check.
3. **[Contribution tiers](../../CONTRIBUTING.md#contribution-tiers)** — reviewer → subsystem owner → core.

## Project board

Track work on the **[Stage 18 Co-Builders](https://github.com/users/warheart1984-ctrl/projects/2)** GitHub Project (issues #2–#8 on the board):

- Columns: **Backlog** → **In Progress** → **Review** (rename default Status options in project settings if needed)
- Setup (maintainers): [`.github/community/SETUP_PROJECT_BOARD.md`](../../.github/community/SETUP_PROJECT_BOARD.md)

## Open entry tickets (2026-06-07)

| # | Issue | Labels / focus |
|---|--------|----------------|
| 2 | [Async diplomacy workflow family](https://github.com/warheart1984-ctrl/Project-Infinity1/issues/2) | `good first issue`, `help wanted`, `python`, `governance`, `civilizational-arc` |
| 3 | [Harden constitutional evolution proofs](https://github.com/warheart1984-ctrl/Project-Infinity1/issues/3) | `help wanted`, `python`, `governance` |
| 4 | [Infinity Pilot Docker multi-tenant](https://github.com/warheart1984-ctrl/Project-Infinity1/issues/4) | `help wanted`, `docker`, `documentation` |
| 5 | [Governance dashboard operator guide](https://github.com/warheart1984-ctrl/Project-Infinity1/issues/5) | `good first issue`, `help wanted`, `documentation`, `governance` — **delivered in-repo:** [GOVERNANCE_DASHBOARD_OPERATOR_GUIDE.md](../operators/GOVERNANCE_DASHBOARD_OPERATOR_GUIDE.md) + [proof](../proof/platform/CO_BUILDER_CIVILIZATIONAL_ARC_SMOKE_V1_PROOF.md) |
| 6 | [Norm federation chaos tests](https://github.com/warheart1984-ctrl/Project-Infinity1/issues/6) | `help wanted`, `python`, `chaos-testing`, `governance` |
| 7 | [Observe/adopt API doc for integrators](https://github.com/warheart1984-ctrl/Project-Infinity1/issues/7) | `good first issue`, `help wanted`, `documentation`, `civilizational-arc` |
| 8 | [Civilizational arc smoke target](https://github.com/warheart1984-ctrl/Project-Infinity1/issues/8) | `good first issue`, `help wanted`, `python`, `governance` — **smoke proven:** [CO_BUILDER_CIVILIZATIONAL_ARC_SMOKE_V1_PROOF.md](../proof/platform/CO_BUILDER_CIVILIZATIONAL_ARC_SMOKE_V1_PROOF.md) |

Issue bodies and acceptance criteria live in [`.github/community/issues/`](../../.github/community/issues/).

## Recommended first PR flow

```bash
git checkout -b co-builder/issue-N-short-name
# ... change ...
make civilizational-arc-smoke   # when touching arc subsystems; see issue for full gate
python -m pytest tests/...      # issue-specific tests
```

In the PR description:

- Link the issue (`Fixes #N` or `Refs #N`)
- Label claims: `asserted` / `proven` / `rejected` per [`REPO_PROOF_LAW.md`](../../REPO_PROOF_LAW.md)
- Paste gate output (or trust bundle path if applicable)

## Law and proof

- [`META_ARCHITECT_LAWBOOK.md`](../../META_ARCHITECT_LAWBOOK.md)
- [`REPO_PROOF_LAW.md`](../../REPO_PROOF_LAW.md)
- Arc stages: [`docs/runtime/AAIS_CIVILIZATIONAL_STAGES.md`](../runtime/AAIS_CIVILIZATIONAL_STAGES.md)
- Pilot evidence: [`docs/audit/CIVILIZATIONAL_ARC_PILOT_EVIDENCE_2026-06-07.md`](../audit/CIVILIZATIONAL_ARC_PILOT_EVIDENCE_2026-06-07.md)

## Pin the discussion (maintainers)

GitHub does not expose a public API to pin discussions. After creating discussion **#9**:

1. Open https://github.com/warheart1984-ctrl/Project-Infinity1/discussions/9
2. **Pin discussion** from the discussion menu (or Discussions → pin on repo index)

This keeps the co-builder call visible to new contributors.
