# AI Mechanic Trust Bundle (stub)

```text
claim_label: asserted
why_short: |
  Post-MVP Mechanic hardening adds trace ingest, report mode,
  review-gated apply, and chat enforcement hook.
  Single-machine pytest + mechanic-gate only at this stage.
proof_links:
  - docs/proof/mechanic/STAGE1_PROOF_BUNDLE.md
  - docs/proof/mechanic/dogfood/MECHANIC_DOGFOOD_REPORT.md
none_yet: false
override_command: make mechanic-gate
override_breaks_blueprint: false
debt_ticket_ref: MECH-XM-01
created_at_utc: 2026-05-31T00:00:00Z
updated_at_utc: 2026-05-31T00:00:00Z
author: mechanic-hardening-agent
context: post-MVP AI Mechanic STAGE1
```

Cross-machine replay remains **debt** until `cross_machine/REPLAY_MANIFEST.template.json` is activated on a second host.
