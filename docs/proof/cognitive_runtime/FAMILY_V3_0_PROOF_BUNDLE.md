# Nova Cortex v3.0 — Persistent Narrative Continuity — Proof Bundle

**Milestone:** Nova Cortex v3.0 — **Persistent Narrative Continuity**

**Claim:** Nova maintains a governed journey across session boundaries via observe-only Narrative (not a second authority), with durable store, rehydration, and automated continuity A/B proof.

**Status:** `proven` (single-machine persistence + A/B + identity guard). Operator continuity study and wolf metal reboot: **debt**.

## Scope

| Deliverable | Path |
|-------------|------|
| Nova Cortex v3.0 family | [src/cog_runtime/__init__.py](../../src/cog_runtime/__init__.py) |
| Narrative v1.0 | [src/cog_runtime/narrative.py](../../src/cog_runtime/narrative.py) |
| Durable store | [src/cog_runtime/narrative_store.py](../../src/cog_runtime/narrative_store.py) |
| Continuity A/B | [src/cog_runtime/narrative_continuity.py](../../src/cog_runtime/narrative_continuity.py) |
| Narrative proof | [NARRATIVE_V1_PROOF_BUNDLE.md](./NARRATIVE_V1_PROOF_BUNDLE.md) |
| Next evidence plan | [NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md](./NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md) |
| Constitutional stack | [NOVA_CORTEX.md](../../docs/runtime/NOVA_CORTEX.md) |

## Architectural claim

```text
Spine → Jarvis → Nova Cortex → Narrative
```

Narrative **observes · synthesizes · records**. It does not route, authorize, or execute.

## Verification

```bash
pytest tests/test_narrative_runtime.py tests/test_narrative_store.py tests/test_narrative_continuity_proof.py tests/test_capability_governance.py tests/test_integration_cog_runtimes.py -q

python .github/scripts/check-nova-narrative-continuity.py
python .github/scripts/check-nova-cortex-governance.py

python -c "from src.cog_runtime import nova_cortex_spec; s=nova_cortex_spec(); print(s['version'], s.get('milestone'))"
```

## Debt (next evidence, not new runtimes)

- Multi-turn companion fixture with simulated session reset
- Operator rubric: "continuing vs restarting" conversation
- Cross-machine wolf boot narrative rehydration

See [NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md](./NARRATIVE_CONTINUITY_EVIDENCE_PLAN.md).
