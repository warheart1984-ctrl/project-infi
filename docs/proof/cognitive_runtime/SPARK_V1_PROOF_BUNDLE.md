# Spark v1 — Constitutional Cognitive Pipeline Proof Bundle

**Claim:** The composed turn runtime binds cortex lobes, Jarvis routing, memory board, generation gate, agency preservation, and ledger monotonicity into a single ignition sequence where the LLM renders from read-only coherence projection — not beside the cortex.

**Status:** `asserted` (single-machine pytest). Cross-machine wolf boot not filed.

## Ignition sequence

```
Turn →
  Spine (Wolf → ARIS → Jarvis) →
    Cortex (Attention → Memory → Deliberation → Reflection) →
      Coherence Projection →
        LLM Renderer (Jarvis modular pipeline) →
          Generation Gate →
            Agency Preservation →
              Ledger Append (monotonic) →
              Self-Tuning (performance metric) →
                Speaking Runtime →
                  Output
```

## Stage map

| # | Stage | Module | Enforced in |
|---|-------|--------|-------------|
| 1 | Coherence Projection Layer | [coherence_projection.py](../../src/cog_runtime/coherence_projection.py) | [spark_pipeline.py](../../src/cog_runtime/spark_pipeline.py), [jarvis_modular.py](../../src/jarvis_modular.py) |
| 2 | Spine Doctrine | [spine_pipeline.py](../../src/cog_runtime/formal/spine_pipeline.py) | [aais_composed_runtime.py](../../src/aais_composed_runtime.py) |
| 3 | Generation Gate | [generation_gate.py](../../src/cog_runtime/formal/generation_gate.py) | API stream + composed turn (when `speak_body` present) |
| 4 | Agency Preservation | [turn_agency.py](../../src/cog_runtime/formal/turn_agency.py) | [spark_pipeline.py](../../src/cog_runtime/spark_pipeline.py) |
| 5 | Ledger Monotonicity | [distributed_ledger.py](../../src/cog_runtime/formal/distributed_ledger.py) | [spark_pipeline.py](../../src/cog_runtime/spark_pipeline.py) |
| 6 | Self-Tuning | [tuning.py](../../src/cog_runtime/tuning.py) | Cortex finalize + spark pipeline |
| 7 | Memory Board Cues | [memory.py](../../src/cog_runtime/memory.py) | Board-primary `normalize_cortex_memory_cues(board)` |

## CPL contract (read-only)

```python
build_coherence_projection_from_cortex(cortex_state) → {
    "focus", "intent", "narrative", "memory_cues", "deliberation", "read_only": True
}
```

Injected into provider messages via `NovaCoherenceProjectionModule` before generation.

## Verification

```bash
bash scripts/verify-composed-turn-spark.sh
```

Or:

```bash
pytest tests/test_spark_pipeline.py tests/test_aais_composed_runtime.py tests/test_coherence_projection.py -q
```

## Evidence gaps (debt)

- Cross-machine ledger merge under wolf boot
- Live provider deliberation with session-bound keys (plumbing asserted; remote API not proven here)
- UI surfacing of `coherence_projection` block in compose receipt (backend only today)
