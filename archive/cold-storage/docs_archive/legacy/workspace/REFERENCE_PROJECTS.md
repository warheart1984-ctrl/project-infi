# Jarvis Reference Projects

This repo is the active product shell.

Active base:

- `AAIS-main`

Reference-only or non-canonical projects mentioned in current AAIS docs:

- `C:\Users\randj\Desktop\project infi\Ui jarvis`
- `C:\Users\randj\Desktop\project infi\code\code`
- `C:\Users\randj\Desktop\project infi\jarvis\jarvis`
- `C:\Users\randj\Desktop\project infi\NVIDIA`
- `mystic`
- `Spiral-Companion-main`
- `Nova, The North Star`
- `God engine`
- `project`

Evidence note:

- the first four entries are explicit path-based sibling references
- the later entries are documented in [AAIS_CANONICAL_MAP.md](../runtime/AAIS_CANONICAL_MAP.md)
- not every sibling project is directly visible from the current `AAIS-main` checkout
- presence in docs does not mean canonical ownership or live verification
- current sibling-folder documentation gaps are tracked in
  [SIBLING_PROJECT_DOCUMENTATION_AUDIT.md](SIBLING_PROJECT_DOCUMENTATION_AUDIT.md)
- the deeper current-truth pass for the `jarvis` sibling is tracked in
  [JARVIS_SIBLING_TRUTH_AUDIT.md](JARVIS_SIBLING_TRUTH_AUDIT.md)
- the deeper current-truth pass for the `mystic` sibling is tracked in
  [MYSTIC_SIBLING_TRUTH_AUDIT.md](MYSTIC_SIBLING_TRUTH_AUDIT.md)

## What AAIS-main should keep owning

- Local Flask backend and the tuned laptop runtime
- The real web app shell and personal-use startup flow
- The operator-facing Jarvis console
- The stable local model integration

## What to borrow from Ui jarvis

- The Jarvis identity
- The voice-first interaction idea
- The glowing orb / command-deck visual language

Borrowed now:

- chat-first home screen
- orb-style console centerpiece
- browser voice input
- optional browser speech output

## What to borrow from code\code

- Provider abstraction patterns
- Clean separation between chat UI and model backends
- Future retrieval and tool-routing ideas

Recommendation:

- Use it as an architecture reference, not a replacement repo
- Pull ideas into `AAIS-main` incrementally when they solve a real need

## What to borrow from jarvis\jarvis

- Longer-term ideas around jobs, RAG, and richer orchestration
- Session and assistant feature concepts
- modular memory-board thinking, but only under the canonical
  [JARVIS Memory Board Doctrine](../contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md)

Recommendation:

- Do not adopt it as the base
- It is feature-rich but structurally messy, with nested variants and environments
- Only cherry-pick specific ideas after the AAIS shell is stable
- Treat memory upgrade ideas as governed slot/controller doctrine, not as
  permission to collapse memory into one flat mutable pool

## What to borrow from NVIDIA

- Private API and security patterns
- Research on protected local service boundaries

Recommendation:

- Keep it separate
- Reuse ideas like private route design, auth boundaries, and local-only API thinking if AAIS needs them later

## Additional documented non-canonical projects

### `mystic`

Use as:

- separate project reference
- UI or interaction idea source if a specific pattern is worth importing

Do not use as:

- AAIS runtime authority
- Jarvis shell replacement

### `Spiral-Companion-main`

Use as:

- substantial reference project with its own direction

Do not use as:

- current AAIS runtime truth

### `Nova, The North Star`

Use as:

- cognition-side concept material
- companion-surface thinking

Do not use as:

- live Jarvis routing authority

### `God engine`

Use as:

- historical lineage for orchestration and system-shell thinking

Do not use as:

- maintained runtime base

### `project`

Use as:

- storage/scaffold overflow only if something there is intentionally migrated

Do not use as:

- a current product definition

## Decision

`AAIS-main` becomes the real UI Jarvis.
