# Specialist Registry Spec

Jarvis does not need a thousand heavyweight model runtimes to feel like it has a thousand minds.

The AAIS approach is:

1. Keep a small number of real inference backends.
2. Route each turn through a logical specialist registry.
3. Let the active mode and request shape decide which specialists are active.
4. Return one final Jarvis answer instead of exposing the internal routing.

## What "1000 LLMs" means here

In AAIS, a "specialist" is a logical expert profile, not necessarily a separately loaded model.

That gives us:

- a fast local model for quick replies
- a stronger model path for deeper replies later
- many named specialists layered on top of those real backends

This is cheaper, lighter, and much more realistic for a private local Jarvis.

## Current Specialist Domains

### Writing

Used for scenes, rewrites, continuity, lore, pacing, dialogue, and tone.

Examples:

- `Draft`
- `Lore`
- `Continuity`
- `Dialogue`
- `Emotion`
- `Pacing`
- `Tone`
- `Combat`

### Coding

Used for implementation, debugging, refactors, reviews, tests, and API work.

Examples:

- `Architecture`
- `Implementation`
- `Debug`
- `Testing`
- `Review`
- `Refactor`
- `API Surface`

### Small-LLM Training

Used for local-model work like dataset building, LoRA fine-tuning, evals, compression, and serving.

Examples:

- `Dataset`
- `Prompting`
- `Fine-Tune`
- `Evaluation`
- `Compression`
- `Serving`
- `Safety`

## How Routing Works

Each turn now produces a specialist profile with:

- `domain`
- `focus`
- `specialists`
- `preferred_mode`
- `summary`
- `directive`

That profile is then used by:

- response-mode recommendation
- runtime prompt assembly
- API response traces
- the Jarvis console trace UI

## Important Constraint

This registry is intentionally logical-first.

If we later add more real backends, we can route specific specialists to different model providers or adapters. But the registry already gives us the right abstraction today:

- few real models
- many virtual minds
- one coherent Jarvis
