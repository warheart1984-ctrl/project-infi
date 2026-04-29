# AAIS Repo Lawbook

This file is the authoritative source of all project laws.
If a law is not listed here, it is not considered active.

This is the one-file lawbook for the repository.

Its job is simple: give you one place to find the active laws, doctrines, and
governing contracts that shape how this project is supposed to behave.

This file is a front door, not a replacement for the source laws.
When there is any ambiguity, the source file linked in each section is the
authority.

## How To Use This File

Use this file when you need to answer questions like:

- What rules define this repo?
- Which law applies to this kind of change?
- Where is the real source document for that law?

Start here, then jump to the linked source file for the full contract.

## Priority Rule

Not every governing file does the same job.

Use this order when deciding what to trust first:

1. live runtime code
2. active law and contract docs
3. repo-level doctrine and canonical project docs
4. archive and lineage material

This order is also consistent with the [AAIS Doc Protocol](docs/contracts/AAIS_DOC_PROTOCOL.md).

## Direct Repo Laws

These are the clearest repo-wide laws in the project.

### 1. Foundation Laws

**What it governs:** the non-negotiable base rules for what may enter and operate inside the system.

**Core idea:** the system should not rely on trust in any one component. Entry, operation, and change all require enforced structure.

**Source:** [docs/contracts/CUOS_FOUNDATION_LAWS.md](docs/contracts/CUOS_FOUNDATION_LAWS.md)

### 2. Seam Law

**What it governs:** how seams are detected, classified, pressure-tested, closed, and proven closed.

**Core idea:** a seam is a latent failure surface at a boundary, not just a bug. If it cannot be bounded and explained, it is still open.

**Source:** [docs/contracts/SEAM_LAW.md](docs/contracts/SEAM_LAW.md)

### 3. External Suggestion Admission Rule

**What it governs:** how outside ideas, proposals, and imported architecture are handled.

**Core idea:** suggestion is not truth. Conversation is not admission. Law decides entry.

**Source:** [docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)

### 4. README Law v1

**What it governs:** how README files must be written.

**Core idea:** explain the system for a human before explaining the architecture for an insider.

**Source:** [docs/contracts/README_LAW_V1.md](docs/contracts/README_LAW_V1.md)

### 5. Cognitive Bridge Runtime Law

**What it governs:** the only legal ingress for governed cognitive packets.

**Core idea:** no proposal, lane, or downstream reasoning surface may become runtime motion until the bridge has normalized it, attached law, and issued a bounded decision.

**Source:** [docs/contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md](docs/contracts/AAIS_COGNITIVE_BRIDGE_RUNTIME_LAW.md)

### 6. Project Infi Runtime Law

**What it governs:** the law substrate for repo actions, runtime actions, verification, admission, observability, and fail-closed behavior in the Project Infi runtime.

**Core idea:** entry, action, outcome, recordkeeping, observability, and failure behavior are all governed explicitly instead of being left to scattered local checks.

**Source:** [src/project_infi_law.py](src/project_infi_law.py)

## Governing Doctrines And Protocols

These are not always named “law,” but they act as governing contracts for major repo boundaries.

### 7. AAIS-UL Doctrine

**What it governs:** the shared structural language used before modules, tools, provider previews, and adaptive subsystems move outward.

**Core idea:** nothing enters raw. Structure comes before expansion. Visibility is part of truth.

**Source:** [docs/contracts/AAIS_UL_DOCTRINE.md](docs/contracts/AAIS_UL_DOCTRINE.md)

### 8. AAIS Module Governance Protocol

**What it governs:** how modules are admitted into the system.

**Core idea:** no module may operate unless it passes governance law and the CISIV stage gate.

**Source:** [docs/contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md](docs/contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md)

### 9. Jarvis Memory Board Doctrine

**What it governs:** how memory is structured, upgraded, migrated, and controlled.

**Core idea:** memory is not one flat bank. It is a board with fixed slot purpose, governed install rules, and lawful migration.

**Source:** [docs/contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md](docs/contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md)

### 10. AAIS Doc Protocol

**What it governs:** how documentation should be read, trusted, and layered.

**Core idea:** docs are authoritative in layers, not all at once.

**Source:** [docs/contracts/AAIS_DOC_PROTOCOL.md](docs/contracts/AAIS_DOC_PROTOCOL.md)

### 11. Jarvis Protocol

**What it governs:** the common runtime language between UI, memory, tools, specialists, and model backends.

**Core idea:** one turn is a structured protocol with named channels, not a loose pile of strings.

**Source:** [docs/contracts/JARVIS_PROTOCOL.md](docs/contracts/JARVIS_PROTOCOL.md)

### 11. Jarvis Reasoning Protocol

**What it governs:** the bounded operator-facing reasoning object used during a turn.

**Core idea:** reasoning must stay inspectable and bounded. It must not become hidden chain-of-thought or a second authority layer.

**Source:** [docs/contracts/JARVIS_REASONING_PROTOCOL.md](docs/contracts/JARVIS_REASONING_PROTOCOL.md)

### 12. AAIS Capability Module Spec

**What it governs:** the boundary contract for external capability execution.

**Core idea:** a capability module does one job only: translate governed AAIS intent into deterministic AAIS-native results.

**Source:** [docs/contracts/AAIS_CAPABILITY_MODULE_SPEC.md](docs/contracts/AAIS_CAPABILITY_MODULE_SPEC.md)

## Runtime Enforcement Files

These files are not just references. They are live enforcement surfaces that turn the laws above into runtime behavior.

### Admission And Status Enforcement

- [src/module_governance.py](src/module_governance.py)
  Admits modules, records runtime signals, and changes module status under pressure.
- [src/phase_gate.py](src/phase_gate.py)
  Enforces maturity/admission phase before execution or routing.
- [src/verification_gate.py](src/verification_gate.py)
  Blocks or admits based on verification outcomes.

### Boundary And Safety Enforcement

- [src/immune_protocol.py](src/immune_protocol.py)
  Detects packet anomalies and violations and applies bounded responses.
- [src/memory_board_enforcer.py](src/memory_board_enforcer.py)
  Forces memory operations through governed boundaries.
- [src/governance_layer.py](src/governance_layer.py)
  Persists governance events, promotion requests, and break-glass state.

### Runtime Law And State Enforcement

- [src/project_infi_law.py](src/project_infi_law.py)
  Applies runtime law to Project Infi actions and verification.
- [src/project_infi_state_machine.py](src/project_infi_state_machine.py)
  Carries the governed runtime cycle shape used by that law.

## One-Sentence Summary Of The Repo

This repo is governed by a simple pattern:

Nothing important should enter raw, act without admission, mutate silently, or fail without a visible rule explaining why.

## Source Law List

For quick scanning, these are the main law-bearing files collected in this lawbook:

- [docs/contracts/CUOS_FOUNDATION_LAWS.md](docs/contracts/CUOS_FOUNDATION_LAWS.md)
- [docs/contracts/SEAM_LAW.md](docs/contracts/SEAM_LAW.md)
- [docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md](docs/contracts/EXTERNAL_SUGGESTION_ADMISSION_RULE.md)
- [docs/contracts/README_LAW_V1.md](docs/contracts/README_LAW_V1.md)
- [docs/contracts/AAIS_UL_DOCTRINE.md](docs/contracts/AAIS_UL_DOCTRINE.md)
- [docs/contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md](docs/contracts/AAIS_MODULE_GOVERNANCE_PROTOCOL.md)
- [docs/contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md](docs/contracts/JARVIS_MEMORY_BOARD_DOCTRINE.md)
- [docs/contracts/AAIS_DOC_PROTOCOL.md](docs/contracts/AAIS_DOC_PROTOCOL.md)
- [docs/contracts/JARVIS_PROTOCOL.md](docs/contracts/JARVIS_PROTOCOL.md)
- [docs/contracts/JARVIS_REASONING_PROTOCOL.md](docs/contracts/JARVIS_REASONING_PROTOCOL.md)
- [docs/contracts/AAIS_CAPABILITY_MODULE_SPEC.md](docs/contracts/AAIS_CAPABILITY_MODULE_SPEC.md)
- [src/project_infi_law.py](src/project_infi_law.py)
