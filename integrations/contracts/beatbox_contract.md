# Beatbox Contract

This file defines the adapter contract for Beatbox-style audio generation.

The goal is to force future provider code to fit the repo's slot instead of
letting external code dictate the system shape.

## Slot

- adapter path: `external/ai/beatbox/adapter.py`
- primary seam: `BeatboxAdapter`
- safe fallback: `SimpleBeatboxFallback`

## Input

Providers wired through the adapter must accept a mapping with:

- `narrative_state`
  - current story or scene state to sonify
- `emotion`
  - emotional target for the generated audio
- `pacing`
  - rhythm or tempo guidance

Additional fields are allowed, but those three are the minimum required
contract.

## Output

The adapter normalizes provider output into this shape:

```json
{
  "audio_file": "string | null",
  "output": "string | null",
  "duration": 0.0,
  "metadata": {},
  "status": "ok | fallback | failed",
  "reason": "string | null"
}
```

## Field Rules

- `audio_file`
  - canonical output path or file name for the generated audio artifact
- `output`
  - compatibility alias for `audio_file`
- `duration`
  - generated audio length in seconds when known
- `metadata`
  - provider-specific details that do not break the shared contract
- `status`
  - `ok` for normal provider output
  - `fallback` when the fallback path handled the request
  - `failed` when no lawful output could be produced
- `reason`
  - failure reason when `status=failed`

## Failure Rules

- invalid input must fail closed with `reason=invalid_input`
- missing providers must fail closed with `reason=no_provider`
- provider exceptions should fall through to the fallback when one exists
- fallback failures must still return a normalized failure object

## Compatibility Rules

- a future provider may return `audio_file` or legacy `output`
- the adapter must normalize both into the canonical shape above
- provider code must not bypass the adapter and write directly into runtime
  callers

## Migration Rule

When external Beatbox code arrives:

1. fit it behind `BeatboxAdapter`
2. keep the adapter contract stable
3. preserve the fallback path
4. add or update tests before broader wiring

## Current Scope

This contract prepares the slot only.

It does not yet wire Beatbox into:

- the Jarvis runtime
- Nova
- workflow execution
- frontend playback surfaces
