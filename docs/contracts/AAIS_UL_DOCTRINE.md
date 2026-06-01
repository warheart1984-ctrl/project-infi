# AAIS-UL Doctrine

AAIS-UL is the shared structural language inside AAIS.

It exists so modules, tools, provider previews, and future adaptive subsystems
arrive in one inspectable payload shape before Jarvis sends anything outward.

Core doctrine:

- Python is the vessel. UL is the law inside it.
- Nothing enters Jarvis raw. Everything passes through adaptation.
- Structure comes before expansion.
- The core stays stable while approved modular zones evolve.
- Visibility is part of truth.

[Stabilize and Free](../spine/STABILIZE_AND_FREE.md) is the operator-facing consequence of UL.

UL stabilizes the system first by carrying structure, law, and visibility.
Only after that stability exists should AAIS free the operator from carrying correctness, flow, and reference manually.

## Three UL Layers Inside AAIS

The authoritative UL documentation (`ProjectInfinity_UL_Documentation.pdf`) defines
governed runtime law. AAIS implements it through three cooperating layers:

1. **Governed cycle** — binary and meta operators (`0001`, `1000`, `1001`, `1010`,
   `1111`, `0001'`, `∆`, `Λ`, `Γ`) that verify, judge, reckon debt, admit state,
   stabilize, bind, and gate the next mutation.
2. **Command substrate** — minimal UL grammar (`Actor Verb Multiplier`) with
   AST-native verb capabilities, default-deny posture, and audit on every dispatch.
3. **Payload adaptation** — shared inspectable envelope (`source`, `kind`, `section`,
   `data`, `metadata`) so nothing enters Jarvis raw.

Layer 1 and 2 carry law. Layer 3 carries structure and visibility.

## Live Implementation

### Governed cycle and law substrate

- [src/project_infi_state_machine.py](../../src/project_infi_state_machine.py) — canonical UL runtime cycle
- [src/project_infi_law.py](../../src/project_infi_law.py) — shared law substrate for repo and runtime actions
- [ProjectInfinity_UL_Documentation.pdf](../../ProjectInfinity_UL_Documentation.pdf) — authoritative UL spec

### Command substrate (ForgeGate)

- [aris/ul_substrate.py](../../aris/ul_substrate.py) — governed command grammar and verb capabilities
- [aris/ul_lang.py](../../aris/ul_lang.py) — general-purpose UL language layer (dev tooling)

### Payload adaptation and runtime wrapping

- [src/aais_ul.py](../../src/aais_ul.py)
- [src/aais_ul.json](../../src/aais_ul.json) — doctrine sections, laws, and object model
- [src/aais_ul_substrate.py](../../src/aais_ul_substrate.py)
- [src/chat_turn_governance.py](../../src/chat_turn_governance.py) — ordinary chat-turn UL preview and CISIV-staged admission
- [src/jarvis_modular.py](../../src/jarvis_modular.py)
- [src/jarvis_protocol.py](../../src/jarvis_protocol.py)
- [src/cognitive_bridge.py](../../src/cognitive_bridge.py)
- [src/governed_direct_pipeline.py](../../src/governed_direct_pipeline.py)
- [src/jarvis_operator.py](../../src/jarvis_operator.py)
- [src/ugr/unified_runtime.py](../../src/ugr/unified_runtime.py)
- [src/capability_service_bridge.py](../../src/capability_service_bridge.py)
- [src/capability_module.py](../../src/capability_module.py)
- [src/ugr/operator_console/snapshot.py](../../src/ugr/operator_console/snapshot.py)

## Ordinary Chat-Turn Admission (CISIV verification)

Every non-tool, non-Super-Nova chat reply passes through Project Infi admission after generation:

1. **Generate** — modular preview is built and stored (`implementation` stage).
2. **Admit** — `finalize_chat_turn_admission()` runs the governed cycle with
   `surface=chat_turn`, `action_id=chat_reply`, and CISIV stage `verification`.
3. **Expose** — `law_enforcement`, `law_event_log`, and `response_trace.chat_turn_admission`
   are returned on the chat payload; failed admission fails closed with HTTP 409.

Sync and stream chat paths both call the same admission helper. Tool-result turns and
Super-Nova turns keep their existing specialized admission paths.

## Forge And Repo Mutation Admission

Forge contractors, evolve handoffs, and patch-review lifecycle actions route through
Project Infi with CISIV staging via [src/forge_repo_governance.py](../../src/forge_repo_governance.py):

| Path | CISIV stage | Surface |
|---|---|---|
| Forge `analyze` / ForgeEval | concept | `forge_contractor` / `forge_eval` |
| Forge `generate_*` | structure | `forge_contractor` |
| Forge `repo_manager` | implementation | `forge_contractor` |
| Patch review create/preview | structure | `repo_action` |
| Patch review decision | verification | `repo_action` |
| Patch review apply | implementation | `repo_action` (+ repo finalize) |
| Evolve job handoff | structure | `evolve_contractor` |

## Canonical CISIV Source

All AAIS surfaces should import stage names, labels, aliases, and lifecycle inference from
[src/cisiv.py](../../src/cisiv.py). Module governance and the run ledger no longer carry
duplicate stage constants.
