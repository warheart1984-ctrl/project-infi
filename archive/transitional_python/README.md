# Transitional Python Archive

This folder contains root-level Python files that were physically moved out of
the repository root after a low-risk reference sweep.

## Why They Were Moved

These files were:

- loose at the repo root
- not part of the current runtime entry path
- not referenced by the active repo reading or execution surfaces

They are retained for recovery, comparison, or future archaeology, but they are
not part of the active root structure anymore.

## Current Contents

- `aais_evolving_protocol.py`
- `aais_provider_fabric.py`
- `aais_runtime.py`
- `nova_anchors_and_membranes.py`

## Rule

If one of these files ever returns to active use, it should come back through
an owned runtime, package, or subsystem path instead of drifting back into the
repo root without explanation.
