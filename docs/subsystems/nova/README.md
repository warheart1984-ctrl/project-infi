# Nova Subsystem

This folder contains the active Nova subsystem docs that belong inside the live
AAIS documentation tree.

## What Nova Is

Nova is a bounded companion surface under Jarvis authority.
Nova may interpret, but Jarvis must authorize.

## Active Docs In This Folder

- [TINY_NOVA_CANONICAL.md](./TINY_NOVA_CANONICAL.md)
  - current canonical source of truth for the active Nova line
- [NOVA_HUMAN_GUIDE.md](./NOVA_HUMAN_GUIDE.md)
  - human explanation of Nova behavior and boundaries
- [NOVA_AI_OPERATING_CONTRACT.md](./NOVA_AI_OPERATING_CONTRACT.md)
  - builder-facing operating rules for Nova
- [NOVA_STAGE_SPEC.md](./NOVA_STAGE_SPEC.md)
  - stage taxonomy and technical boundaries

## Future Nova Material

The following Nova-adjacent docs are not active subsystem truth and were moved
out of this folder intentionally:

- [../../_future/super_nova_expansion/SUPER_NOVA_CANONICAL.md](../../_future/super_nova_expansion/SUPER_NOVA_CANONICAL.md)
- [../../_future/biometric_inputs/NOVA_TOUCH_INPUT_GUIDE.md](../../_future/biometric_inputs/NOVA_TOUCH_INPUT_GUIDE.md)

Current live interaction truth is still keystroke-first.

That means touch remains design-only until runtime code and tests explicitly
install it.

Current Super Nova truth is:

- live as a guarded lane
- explicit activation required
- immune coupling is observe-only through protocol signals
- broader predictor/invariant-driven immune automation remains future work

## Canonical Rule

The active canonical doc in this folder is
[TINY_NOVA_CANONICAL.md](./TINY_NOVA_CANONICAL.md).

If Nova docs conflict with runtime code, runtime code wins.

## Nova Cortex PDF — multi-substrate boundary (Stage 15)

The [Nova Cortex PDF](../../../Nova%20Cortex_%20A%20Constitutional,%20Runtime%E2%80%91Composed%20Cognitive%20Architecture%20for%20Synthetic%20Minds.pdf) §11
future work (multi-substrate cognition, distributed cortex clusters) is **not** implemented as
new diplomacy lobes in [`src/cog_runtime/nova.py`](../../../src/cog_runtime/nova.py).

| Concern | Layer | Module |
|---------|-------|--------|
| Modular lobes (attention, deliberation, memory, speaking) | Nova Cortex | `cog_runtime/nova.py` |
| Cross-substrate accords, drift, dual-gate adoption | Civilizational governance (Stage 15) | `inter_substrate_diplomacy_runtime.py` |
| Authorization / no self-expansion | Tri-Core | `jarvis_diplomacy_authority.py` |

Nova may **interpret** substrate posture for operators; Jarvis must **authorize** diplomatic adoption.
ISD is the governance answer to multi-substrate coordination — not an extension of cortex lobes.

## Pending Future Ideas

- [Reflection Runtime Organ](../../_future/ideas_pending/REFLECTION_RUNTIME_ORGAN.md)
  — Alt-5 wave 2; active doc [REFLECTION_RUNTIME_ORGAN.md](./REFLECTION_RUNTIME_ORGAN.md)
- [Memory Runtime Organ](../../_future/ideas_pending/MEMORY_RUNTIME_ORGAN.md)
  — Alt-5 wave 2; active doc [MEMORY_RUNTIME_ORGAN.md](./MEMORY_RUNTIME_ORGAN.md)
- [Human Voice Extraction](../../_future/ideas_pending/HUMAN_VOICE_EXTRACTION.md)
  — concept origin; active doc under [../speakers/HUMAN_VOICE_EXTRACTION.md](../speakers/HUMAN_VOICE_EXTRACTION.md)
