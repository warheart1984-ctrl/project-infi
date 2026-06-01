# AI Mechanic Dogfood Debt Register

| ID | Finding | Severity | Owner | Status |
|----|---------|----------|-------|--------|
| DOGFOOD-GOV-01 | 19× GOV-01 missing decision owner on CI/workflows and model-call chains | high | TBD | open |
| DOGFOOD-RNT-11 | 5× RNT-11 model calls without audit hook metadata in genome | medium | TBD | open |
| DOGFOOD-HUM-03 | Automated model chains lack human_control nodes | high | TBD | open |
| DOGFOOD-HUM-05 | High-impact CI LLM workflow without HITL step | medium | TBD | open |
| DOGFOOD-ADAPTER-01 | `.cursor/` prompt double-scan caused duplicate node id on full-repo scan | medium | TBD | closed (filesystem adapter skip) |
| DOGFOOD-RNT-04 | Cycle risk detected in workflow graph | critical | TBD | open |

Source: [dogfood/MECHANIC_DOGFOOD_REPORT.md](../proof/mechanic/dogfood/MECHANIC_DOGFOOD_REPORT.md) (`asserted`).

Cross-reference: [MECHANIC_CAPABILITY_INVENTORY.md](./MECHANIC_CAPABILITY_INVENTORY.md) entry `MECH-DOGFOOD-01`.
