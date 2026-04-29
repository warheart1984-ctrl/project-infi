# AAIS

AAIS is a local-first assistant runtime built to stay useful when work gets messy.
It gives one governed place to talk to the system, manage memory, review actions, run workflows, and inspect why something was allowed, blocked, or downgraded.

It matters because the project is designed to reduce operator load instead of adding more hidden complexity.
The system is meant to stay readable, bounded, and correct enough that a person can trust what it is doing and catch what it is not doing.

## Key Principle

Stability comes before freedom.

The system should only take on more responsibility after it can stay inside clear rules, explain its behavior, and fail in a controlled way.
If it cannot do that, it should slow down, ask for confirmation, or stop.

## What Is This?

This repository contains the live AAIS application, API, operator console, workflow shell, memory controls, and safety layers.
It also now carries ARIS in embedded form as governed repo-intelligence law instead of leaving ARIS only in archive lineage.

In practical terms, it gives you:

- a conversational operator surface
- governed memory and review flows
- bounded tool and workflow paths
- visible traces when the system changes course
- a local-first runtime that keeps state and authority close to the operator

## Why Is This Different?

Most assistant projects optimize for output first.
AAIS optimizes for behavior first.

That means the system is built to:

- keep one clear operating contract per turn
- separate normal work from risky or experimental work
- show when it reroutes, pauses, or blocks
- preserve operator control instead of hiding decisions in the background

## How Does It Behave?

AAIS is designed to feel steady, not surprising.

When things are normal, it should answer directly and keep moving.
When memory is blocked, context is weak, or a boundary is crossed, it should degrade safely instead of pretending everything is fine.
When a tool or subsystem needs more authority, it should go through governed checks before acting.
Protected Jarvis ingress also uses bridge-issued, time-bound attestation so detached or replayed launches fail closed instead of drifting silently.

## How Does It Work?

At a high level, the system does four things:

1. takes in a request
2. resolves the right response mode and runtime path
3. applies memory, governance, and safety checks
4. returns a result plus trace information for operator surfaces

Later in this repository you will see internal names such as Jarvis, Forge, OTEM, and workflow shell surfaces.
Those are implementation layers inside the system, not the first thing you need to understand to use it.

## System Structure

- `docs/` -> active system truth
- `docs/_archive/` -> historical material
- `docs/_future/` -> planned or not-live material

Only the active documentation tree under `docs/` is authoritative for runtime understanding.
Archive and future material may explain lineage or intent, but they do not define live behavior.

## How Do I Run It?

Fastest local start:

```bash
python -m pip install -e .
python -m aais start --data-dir ./.runtime/aais-data
```

Then open:

- [http://127.0.0.1:8000/app](http://127.0.0.1:8000/app)
- [http://127.0.0.1:8000/app/jarvis](http://127.0.0.1:8000/app/jarvis)
- [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Release prep without launching:

```bash
python -m aais prepare --force-build --data-dir ./.runtime/aais-data
python -m aais doctor --data-dir ./.runtime/aais-data
```

If you use the frontend dev server instead of the packaged shell, the main surfaces are:

- `http://localhost:3000/jarvis`
- `http://localhost:3000/workbench`
- `http://localhost:3000/memory`

## What Should I Read Next?

If you want the current system truth, start here:

1. [AAIS Human Guide](docs/spine/AAIS_HUMAN_GUIDE.md)
2. [AAIS AI Operating Contract](docs/spine/AAIS_AI_OPERATING_CONTRACT.md)
3. [AAIS Master Spec](docs/spine/AAIS_MASTER_SPEC.md)
4. [AAIS Runtime Guide](docs/runtime/AAIS_RUNTIME_GUIDE.md)
5. [AAIS Documentation Map](docs/README.md)

If you want the README writing standard used for this repo, see [README Law v1](docs/contracts/README_LAW_V1.md).

## Technical Notes

The main runtime entry points are:

- `app/main.py` for the packaged shell and workflow infrastructure
- `src/api.py` for the live API surface
- `src/jarvis_operator.py` for core operator/runtime behavior

Important internal implementation layers include:

- Jarvis as the main authority lane
- Forge as a bounded contractor lane
- OTEM as a bounded task/memory support lane
- workflow shell routes under the packaged app

The docs are organized by role:

- `docs/spine/` for canonical project explanation
- `docs/runtime/` for runtime and system references
- `docs/contracts/` for laws and contracts
- `docs/subsystems/` for subsystem-specific packs
- `docs/audit/` for status and audit material
- `docs/_archive/legacy/workspace/` for workspace support and reference material

Anything under `docs/_archive/` is for lineage or reference, not active authority.

## Optional Provider Setup

Claude support ships with the normal Python requirements.

To enable it:

- set `ANTHROPIC_API_KEY` in `.env`
- optionally set `AAIS_CLAUDE_MODEL`
- leave `AAIS_ENABLE_CLAUDE_AUTO_ROUTING=true` if you want remote-eligible `think` and `research` turns to route there automatically

If you want to pin Claude instead of relying on auto-routing, start a session with `provider_mode=claude_first` or pick Claude in the Jarvis Console provider controls.

## Project Laws

This repository already carries project-level operating laws.
Two that matter near the front door are:

- [README Law v1](docs/contracts/README_LAW_V1.md)
- [External Suggestion Admission Rule](docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
- [ARIS Runtime Contract](docs/contracts/ARIS_RUNTIME_CONTRACT.md)
- [AAIS Cognitive Bridge Runtime Law](docs/contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md)

The core doctrine behind the system remains [Stabilize and Free](docs/spine/STABILIZE_AND_FREE.md).

---
There are foundations in this system that are not documented. Some are only discovered.
---
