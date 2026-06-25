# Mission #002 — Nova Integration Reproduction Bundle

## Goal

Reproduce Nova governed integration (SDK + CLI + CRK-1 spec) from scratch, without founder involvement.

## Success Criteria

- [ ] `nova` CLI runs locally
- [ ] `nova generate "…"` returns code and governance receipts
- [ ] At least one invariant blocks an unsafe action
- [ ] Observer can verify behavior using only this repo

## Artifacts

| Path | Purpose |
|------|---------|
| `src/` | Nova SDK implementation |
| `config/` | Invariants + CRK-1 spec |
| `docs/` | Developer documentation |
| `web/` | Marketing site |
| `examples/` | Example governed project |
| `observer/` | Independent verification protocol |

## Reproduction

Follow `observer/REPRO_PROTOCOL.md`.

## Manifest

```yaml
mission: "002"
name: "Nova Integration Reproduction Bundle"
objective: "Founder-independent reproduction of governed Nova SDK + CLI + CRK-1 spec"
reproduction_steps: observer/REPRO_PROTOCOL.md
success_criteria:
  - "Observer runs nova CLI without founder guidance"
  - "Governed code generation with receipts"
  - "At least one invariant enforced"
  - "Continuity snapshot observable"
```
