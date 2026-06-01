# AAIS Composed Turn v1 — Proof Bundle

**Claim:** Jarvis chat (operator + companion + Super Nova) routes every turn through the AAIS Composed Turn Runtime (Spine doctrine, ARIS admission, Nova Face/Cortex/Jarvis), with Super Nova gates before compose and operator fast/instant compose modes for near-instant ingress.

**Status:** `asserted` (single-machine pytest). Cross-machine wolf boot proof not yet filed.

## Scope

| Deliverable | Path |
|-------------|------|
| Composed runtime | [src/aais_composed_runtime.py](../../src/aais_composed_runtime.py) |
| Jarvis chat wiring | [src/api.py](../../src/api.py) (`_configure_cognitive_runtime_turn`, `_require_super_nova_before_composed_turn`) |
| Fast compose path | [src/cog_runtime/nova.py](../../src/cog_runtime/nova.py) (`cortex_fast_path`) |
| Nova Cortex family | [docs/runtime/NOVA_CORTEX.md](../../runtime/NOVA_CORTEX.md) |
| v2.2 lobe proof (related) | [FAMILY_V2_2_PROOF_BUNDLE.md](./FAMILY_V2_2_PROOF_BUNDLE.md) |

## Compose modes

| Mode | When | Cortex behavior |
|------|------|-----------------|
| `instant` | Default Jarvis operator turn | Spine + ARIS + Jarvis face only; no cortex lobes |
| `fast` | `think` mode or explicit `cognitive_runtime: true` (non-decision) | Reasoning + Attention only |
| `full` | Companion, Super Nova (activated), decision frames, `research`/`debug` | Full Nova Cortex router |

## v2.2 invariants (composed turn)

- `super_nova_gate_before_compose` — phase + activation before compose
- `super_nova_activation_cache` — valid activation token satisfies gates until watchdog revokes
- `operator_instant_compose` — every operator turn records Spine + ARIS
- `operator_fast_compose` — think/cognitive operator turns use fast path unless decision frame
- `aris_before_cortex` — ARIS blocks before cortex runs
- `jarvis_authority` — Jarvis retains routing and safety authority

## Verification

```bash
pytest tests/test_aais_composed_runtime.py -q

pytest tests/test_api.py -k "operator_message_records_instant_compose or operator_think_mode_uses_fast_compose or tiny_nova_message or tiny_nova_blocks_raw or super_nova" -q

python -m src.aais_composed_runtime --spec
```

### Expected signals

- Operator `/message`: `aais_composed_turn.compose_mode == "instant"`, `aris_status == "enforced"`
- Operator `think` mode: `compose_mode == "fast"`, runtimes `{jarvis.reasoning, cognitive.attention}`
- Super Nova without activation: `aais_composed_turn` absent, HTTP 409
- Super Nova activated: `compose_mode == "full"`, `nova_face_id == "super_nova"`
- ARIS raw copy block: HTTP 403, `status == "blocked"`, `reason_codes` contains `aris_non_copy_clause`

## Near-instant thought process (design)

Instant compose keeps pre-generation work to:

1. Spine envelope (constant-time doc refs)
2. ARIS admission (dict scan, no I/O)
3. Jarvis face binding (no cortex when `instant`)

Fast compose adds Attention + Reasoning lobes only (typically sub-100ms in pytest). Full compose (companion/Super Nova/decision) runs the complete lobe chain and defers Speaking output to post-generation finalization.

Super Nova activation is near-instant after first explicit activate: subsequent turns reuse the activation token; gates are metadata checks, not model calls.

## Debt

- Cross-machine proof on wolf-cog-os-full installed ISO
- Latency budget enforcement (p95 compose time) in CI
- Parallel lobe execution for full compose mode
