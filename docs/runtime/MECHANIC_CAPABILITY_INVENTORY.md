# AI Mechanic Capability Inventory

| Field | Value |
|-------|-------|
| **Subsystem ID** | `ai_mechanic.v1` |
| **Claim posture** | `asserted` |

## MVP + STAGE1 capabilities

- [x] Process Genome extraction (generic `--repo-path`) — `asserted`
- [x] GOV/RNT/CST/HUM diagnosis catalog (18 rules) — `asserted`
- [x] Dry-run rebuild artifacts — `asserted`
- [x] Runtime profile enforcer — `asserted`
- [x] Governance gate (v1 + v2 fixtures) — `asserted`
- [x] NDJSON trace adapter (`--trace-path`) — `asserted`
- [x] Report mode — `asserted`
- [x] Review-gated apply-review — `asserted` (partial MECH-APPLY-01)
- [x] Chat hook (feature-flagged) — `asserted` (partial MECH-CHAT-01)

## Debt register

| ID | Item | Status | Owner |
|----|------|--------|-------|
| MECH-LLM-01 | LLM process reconstruction | debt | TBD |
| MECH-TRIBAL-01 | Interview/log ingest | debt | TBD |
| MECH-TRACE-01 | Multi-vendor trace normalization | partially closed | TBD |
| MECH-APPLY-01 | Review-gated apply | partially closed | TBD |
| MECH-CHAT-01 | Jarvis api.py wiring | partially closed | TBD |
| MECH-XM-01 | Cross-machine replay | stub only | TBD |
| MECH-DOGFOOD-01 | Self-scan drift remediation | debt — see dogfood report | TBD |

## Verify

```bash
make mechanic-gate
pytest tests/test_mechanic.py tests/test_mechanic_chat_hook.py -q
```

See also: [MECHANIC_DOGFOOD_DEBT.md](./MECHANIC_DOGFOOD_DEBT.md)
