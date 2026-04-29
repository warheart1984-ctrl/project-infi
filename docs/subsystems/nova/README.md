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
