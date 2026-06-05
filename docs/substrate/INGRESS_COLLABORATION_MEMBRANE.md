# Ingress Collaboration Membrane (Human-AI Co-Collaboration Charter)

Normative spec for turn-ingress human–AI collaboration law — maps charter to machine enforcement.

## Authority

| Layer | Path | Role |
|-------|------|------|
| Human charter | `lawbook/HUMAN_AI_CO_COLLABORATION_CHARTER.md` | Collaboration semantics |
| Machine membrane | `src/substrate/ingress/collaboration_membrane.py` | Turn-level invariant checks |
| Ingress surface | `src/chat_turn_governance.py` | `finalize_chat_turn_admission()` |

Subordinate to Meta Architect Lawbook (Charter Article VI). Constitutional spine loads first; collaboration membrane runs at turn ingress alongside `chat_turn_governance`, `memory_governance_membrane`, and `aais_ul_substrate`.

## Invariants (machine-emitted)

| Invariant ID | Charter article | Enforcement |
|--------------|-----------------|-------------|
| `claim_labels` | Art II | `asserted` / `proven` / `rejected` taxonomy |
| `human_authority` | Art I, VI | Human final authority; AI subordinate to lawbook |
| `override` | Art III | Human override path acknowledged |
| `epistemic_escalation` | Art IV | Ambiguity/risk → escalate, not silently assume |
| `reversibility` | Art V | Actions reversible; one-command undo posture |

## Turn ingress

`evaluate_turn_collaboration_membrane()` runs before Project Infi admission in `finalize_chat_turn_admission()`.

- Charter fail to load → refuse turn when `AAIS_REQUIRE_COLLABORATION_CHARTER=1`
- Dev: graceful degrade to `status: absent` when charter missing and flag unset

## Bootstrap

`ensure_collaboration_charter_ready()` in `tests/governance_bootstrap.py` seeds charter readiness for the pytest harness.

## Gate

```bash
python3 tools/governance/check_collaboration_charter.py
```

Makefile target: `collaboration-charter-gate`

## Related

- [CONSTITUTIONAL_LAYER.md](./CONSTITUTIONAL_LAYER.md) — supreme constitutional spine
- [../runtime/STAGE2_COPILOT_DOCTRINE.md](../runtime/STAGE2_COPILOT_DOCTRINE.md) — MA-13 operationalization
