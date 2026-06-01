# Jarvis Reasoning Protocol

The reasoning protocol is the bounded operator-facing reasoning contract inside AAIS.

It is not hidden chain-of-thought.
It is not freeform inner monologue.
It is not a second brain.

It is the inspectable structure Jarvis uses to carry:

- goal
- route choice
- workspace evidence
- risk posture
- action state
- verification targets

through one shared runtime shape.

## Why It Exists

Jarvis already had:

- a message protocol
- a modular provider preview
- guardrail evaluation
- workspace context
- action lifecycle state

What it did not have was one clean reasoning object that explained how those parts line up for the current turn.

The reasoning protocol fills that gap.

## Core Rule

The reasoning protocol must stay bounded and inspectable.

That means:

- it may explain operator-visible reasoning state
- it may not expose hidden chain-of-thought
- it must use canonical runtime truth
- it must not invent a second routing authority

## Canonical Runtime Shape

The live implementation is in:

- [src/jarvis_reasoning_protocol.py](../../src/jarvis_reasoning_protocol.py)

It emits a packet shaped like:

```python
{
    "stage": "orient",
    "goal": "Stabilize OpenRouter-first routing.",
    "mode": "operator",
    "route": {
        "provider": "openrouter",
        "provider_reason": "manual_preference",
        "mode": "operator",
        "specialist_domain": "coding",
        "specialist_focus": "debug_runtime",
    },
    "workspace_refs": [
        {"file_path": "src/api.py"},
        {"file_path": "tests/test_api.py", "symbol": "test_protocol_endpoint"},
    ],
    "risks": [
        {"level": "medium", "message": "Doctrine posture is caution."}
    ],
    "verification_targets": [
        {"target": "tests/test_api.py", "kind": "test_file", "reason": "Likely test seam from the repo map."}
    ],
    "action_state": {
        "stage": "approved",
        "approval_state": "approved",
        "execution_state": "pending",
        "action_id": "action_123",
    },
    "summary": "Goal: Stabilize OpenRouter-first routing. Route: openrouter. Verification targets: 1. Action stage: approved."
}
```

## Stages

The current bounded stages are:

- `observe`
- `orient`
- `decide`
- `act`
- `verify`

These are descriptive stages for operator visibility, not freeform reasoning transcripts.

## Runtime Sources

The reasoning protocol pulls from existing AAIS runtime truth:

- goal from session state
- route from model routing and specialist profile
- workspace evidence from workspace context
- risks from canonical guardrail evaluation and action errors
- verification targets from the repo map and project profile
- action state from the canonical action lifecycle

Memory truth should also respect the
[JARVIS Memory Board Doctrine](JARVIS_MEMORY_BOARD_DOCTRINE.md):

- reasoning should not treat Jarvis memory as one flat bank
- slot purpose should remain fixed across upgrades
- controller approval should gate install, swap, and activation
- slot trust and retrieval role should shape what memory is surfaced
- lower-trust memory may inform the packet, but may not redefine higher-trust
  identity, doctrine, or canonical truth
- migration should only surface as valid when trust class and slot role are
  preserved

This keeps the protocol aligned with Rule 6:

separation preserves intelligence.

Each subsystem keeps its own job, and the reasoning protocol reports across them without replacing them.

## API Surface

The reasoning protocol is exposed through:

- [src/jarvis_protocol.py](../../src/jarvis_protocol.py)
- [src/jarvis_modular.py](../../src/jarvis_modular.py)
- [src/api.py](../../src/api.py)

The main inspection route is:

- `GET /api/jarvis/protocol`
- `GET /api/jarvis/protocol?session_id=<id>`

Session payloads now include:

- `reasoning_protocol`
- `reasoning_packet`
- `reasoning_summary`

## Design Constraints

The reasoning protocol must preserve these constraints:

- one canonical runtime truth
- no duplicate routing authority
- no hidden chain-of-thought exposure
- no provider-specific reasoning format drift
- no UI-only reinterpretation of reasoning state
- no flat-memory assumption that bypasses memory-board trust and slot rules

## Tests

The contract is verified in:

- [tests/test_jarvis_protocol.py](../../tests/test_jarvis_protocol.py)
- [tests/test_api.py](../../tests/test_api.py)

The tests assert:

- protocol spec exposure
- modular preview exposure
- API parity with preview truth
- reasoning summary consistency
- mode and guardrail propagation
