# Cognitive Unified OS — Developer Handbook

> AAIS does not rely on trust. It relies on enforced structure,
> observability, and controlled evolution.

---

## 0. Before You Touch Anything

Read this section first. It answers the four questions every developer
needs on day one.

### What is AAIS?

AAIS (Adaptive Autonomous Intelligence System) is a governed intelligence
platform designed to operate, adapt, and evolve within strictly enforced
structural laws.

- **Adaptive:** Learns from validated outcomes within constrained boundaries
- **Autonomous:** Executes decisions under centralized authority control
- **Intelligence System:** Operates as a coordinated, multi-component
  architecture governed by Foundation Laws

AAIS is a local-first, operator-controlled AI platform. The live product is
built around Jarvis — a runtime that manages AI providers, memory, governance,
and operator-facing surfaces under a single controlled shell.

The system is intentionally sovereign: the operator controls what the AI can
do, how it behaves, and what it remembers. Nothing runs or persists without
passing through the governance and review layers.

### How to run it locally

Run `.\\start-personal.ps1` from the AAIS-main root directory in PowerShell.

Once running, open these in your browser:
- `http://localhost:3000` — the main web app (Jarvis Console + Workbench)
- `http://127.0.0.1:8000/health` — Flask backend health check
- `http://127.0.0.1:6060/health` — service health
- `http://127.0.0.1:6061/health` — service health
- `http://127.0.0.1:6062/health` — service health

### Where to work

The only place you should be making changes is inside `AAIS-main`.
Everything else in the workspace is either a separate project or a
reference archive.

> **Rule of Thumb:** If it's not inside AAIS-main, do not modify it with
> the intention of changing AAIS runtime behavior. Read it for ideas, not
> as the source of truth.

### Where NOT to touch

The workspace contains several other folders. They exist for reference or as
separate products. Do not treat them as part of the live runtime:

- `Ui jarvis` — visual prototype only, not the maintained runtime
- `code\code` — architecture ideas, not a current product
- `jarvis\jarvis` — older feature tree, structurally messy
- `NVIDIA` — separate private API sandbox
- `mystic` — separate small project, not Jarvis

---

## 1. Foundation Laws (Mandatory)

All development within the Cognitive Unified OS must comply with the following
Foundation Laws. These laws are non-negotiable and take precedence over all
architecture, implementation, and system behavior.

Any component, feature, or workflow that violates these laws is considered
invalid and must be redesigned.

### Law 1 — Admission Control Law

Nothing enters. Nothing operates. Without Forge approval.

No component may participate in the Cognitive Unified OS unless it is
Forge-originated or has been processed through Forge and has successfully
passed system evaluation. Any external tool, plugin, workflow, code module,
behavior, or adaptive artifact must be submitted to Forge for evaluation,
redesign, and normalization prior to participation. Components that fail
evaluation are rejected and may not operate within the system until
reprocessed and approved.

### Law 2 — Execution Governance Law

One authority. One role. No drift.

All execution, routing, and system-level decisions must remain under a single
authoritative control layer. Every component must operate only within its
defined role, scope, and purpose, and no component may independently override
authority, expand its function, or assume responsibilities outside its
designated boundaries.

### Law 3 — Observability Law

Nothing happens in the system without visibility.

All system actions, decisions, transformations, and executions must be fully
traceable, inspectable, and recorded in a consistent and unified format. No
operation may occur without producing an observable record.

### Law 4 — Violation Handling Clause

Violation stops execution. Containment prevents spread.

Any component, behavior, or execution that violates the Foundation Laws must
be immediately halted, isolated, and prevented from further participation.
Violations must be recorded, classified, and contained until reprocessed and
approved through Forge.

### Law 5 — Consistent Execution Law

Execution must remain consistent, regardless of path.

All execution paths — including primary, fallback, degraded, and recovery
modes — must produce consistent structure, format, and observable behavior. No
execution path may alter the expected schema, output contract, or trace
integrity.

### Law 6 — Adaptation Constraint Law

Learning is allowed. Structural mutation is not.

Adaptive systems may learn only from validated and approved outcomes and must
not alter core roles, authority boundaries, system structure, or Foundation
Laws. All adaptive changes must remain within predefined constraints and are
subject to Forge oversight.

### Interpretation Rule

If ambiguity exists in implementation or design, the interpretation that most
strictly enforces the Foundation Laws must be chosen. No implementation may
weaken, bypass, or reinterpret these laws in a less restrictive manner.

---

## 2. Forge Outcome Classification Rule

Every artifact submitted to Forge must be classified by outcome.

Artifacts that pass evaluation and normalization are admitted to the
**Hall of Fame** as approved system lineage.

Artifacts that fail evaluation are admitted to the **Hall of Shame** as
rejected lineage and are placed in a non-executable containment state.

**No artifact may exist in an unclassified operational state.**

---

## 3. Canonical Runtime Spine

The main runtime files are:

- `src/api.py`
- `src/conversation_memory.py`
- `src/jarvis_operator.py`
- `src/jarvis_protocol.py`
- `src/jarvis_reasoning_protocol.py`
- `src/jarvis_modular.py`
- `src/provider_registry.py`
- `src/governance_layer.py`
- `src/run_ledger.py`
- `src/patch_review_store.py`
- `frontend/src/pages/JarvisConsole.jsx`
- `frontend/src/pages/Dashboard.jsx`

If a doc says one thing and these files do another, the code is the truth.

---

## 4. Doc Authority Order

The docs in this repo are authoritative in layers, not all at once:

1. Live runtime code
2. Canonical current docs
3. Foundational lineage docs
4. Aspirational or infrastructure docs
5. Outside reference projects

If two sources conflict, the higher layer wins.

---

## 5. State Hygiene Taxonomy

AAIS uses one shared state hygiene taxonomy. Do not collapse these concepts:

- `state_class` — what environment or lane did this record come from?
  (`live`, `demo`, `smoke`, `test`)
- `truth_status` — how authoritative is this record?
  (`canonical`, `derived`, `reference`, `historical`)
- `retention_status` — should this still read like current operator truth?
  (`current`, `archived`, `expired`)

### Shared Projection Helpers

AAIS must not let each surface invent its own meaning for state. The shared
helpers are the authority:

- `is_operator_visible(record)`
- `retention_policy_for(record)`
- `badge_for_state(record)`
- `precedence_rank(source_type, truth_status)`

The UI should render these projections, not reinterpret them.

---

## 6. Knowledge Conflict Rule

Knowledge conflicts resolve by precedence:

1. Canonical override memory
2. Live canonical operator memory
3. Live governance/continuity state
4. Workspace truth
5. Document/reference truth
6. Live research
7. Doctrine/reference docs
8. Review and run history
9. Governance event history

If two sources disagree, the higher precedence source wins.

---

## 7. AAIS-UL Doctrine

AAIS-UL is the shared structural language inside AAIS. It exists so modules,
tools, provider previews, and future adaptive subsystems arrive in one
inspectable payload shape before Jarvis sends anything outward.

**Core doctrine:**
- Python is the vessel. UL is the law inside it
- Nothing enters Jarvis raw. Everything passes through adaptation
- Structure comes before expansion
- The core stays stable while approved modular zones evolve
- Visibility is part of truth

**Live implementation:**
- `src/aais_ul.py`
- `src/jarvis_modular.py`
- `src/jarvis_protocol.py`

---

## 8. Nova / Jarvis Authority Split

**System Law:**

> Nova may interpret. Jarvis must authorize.

- **Nova** provides cognition, persona, and emotional intelligence
- **Jarvis** provides verification, governance, and execution authority

Nova owns: persona, reasoning, and emotional interpretation.
Nova does not own: autonomous execution, tool invocation, verification, or
system authority.

Those functions are exclusively handled by Jarvis.

Nova's internal integrity is protected by anchors and membranes — structural
self-protection baked into each layer, not bolted on top.

Jarvis's external enforcement is protected by angels and wards — runtime
doctrine nodes that catch system-level threats.

---

## 9. OTEM Contract

OTEM (Operator Task Execution Model) is a governed, deterministic,
non-persistent task reasoning lane under Jarvis authority.

**Version ceiling currently active: v5**

**Hard invariants that must never be violated:**
- No memory writes
- No workflow creation
- No run ledger writes
- No persistence
- Session-scoped only
- Proposal only — no direct execution

**Reason-Only Lane:** OTEM reasons about execution contexts, tools, and
workflows without executing them. All suggestions are structured proposals
requiring operator confirmation.

---

## 10. Anti-Drift Contract

The anti-drift layer enforces the active thread contract at the reply layer.

Drift is detected when a reply contains:
- Internal scaffolding or trace leakage
- Generic assistant language instead of Jarvis voice
- Ready-stance softening instead of decision-oriented output
- Execution claims inside reason-only lanes

**Severity model:** `warn → clamp → block`

Blocked replies are replaced with a minimal Jarvis-owned fallback. The fallback
is contract-label-specific — Jarvis stays in character, not generic.

---

## 11. Corrigibility Contract

The corrigibility engine handles explicit operator corrections.

**Three actions:**
- `self_correct` — queues a correction for the next generated reply
- `revert` — rolls back the last assistant turn and optionally queues guidance
- `soft_pause` — routes through System Guard to pause new Jarvis turns

**Three severity levels:** `mild (0.68)`, `strong (0.86)`, `override (0.98)`

Corrections are applied silently in the next reply. Jarvis does not narrate
the correction — it just answers correctly.

---

## 12. Workbench Contract

The Workbench should show:
- Live operator truth by default
- Execution cockpit state
- Review/apply history
- Memory governance
- Governance posture
- Workspace lane
- Knowledge authority summary

It must not make demo or browser-verification residue look like live operator
truth.

---

## 13. Store Lifecycle Rules

### Memories
- Live active memories are visible operator truth
- Archived memories stay readable but stop acting like current truth
- Non-live memories should be compacted out of current views

### Patch Reviews
- Proposal is not authority
- Accepted review is the apply gate
- Non-live review artifacts should archive out of current operator views

### Run Ledger
- Open live runs stay visible
- Stale non-live open runs should expire
- Completed runs remain historical evidence, not current state

### Governance
- Active break-glass and live policy posture are current truth
- Governance events are audit history
- Non-live governance artifacts can be pruned without losing live posture

---

## 14. Merge Rules

When borrowing from sibling projects or older docs:
- `AAIS-main` stays the active base
- Reference repos are sources of ideas, not replacements
- Nothing enters Jarvis raw
- New subsystems must speak the existing Jarvis protocol or UL shape
- Visible guardrail state must come from one canonical runtime evaluation
- External ideas may enrich the shell, but they do not redefine Jarvis identity

---

## 15. Security Closeout

The remaining manual security closeout is:

- Rotate the OpenRouter key

The repo includes a local helper for this process, but account-side key
revocation still must happen in the OpenRouter dashboard.

---

## 16. Decision Rule

Before accepting any doc-driven idea into AAIS, ask:

- Is it live truth, lineage, or aspiration?
- Where does it plug into the current spine?
- Does it preserve protocol and guardrail integrity?
- Is it inspectable?
- Is `AAIS-main` still the owning shell after the change?

If those answers are unclear, the idea is not ready yet.

---

## Reading Order

If someone needs to understand the repo quickly, use this order:

1. `README.md`
2. `AAIS_SYSTEM_HANDBOOK.md`
3. `docs/README.md`
4. `AAIS_CANONICAL_MAP.md`
5. `CUOS_FOUNDATION_LAWS.md`
6. `JARVIS_PROTOCOL.md`
7. `AAIS_UL_DOCTRINE.md`
8. `SPECIALIST_REGISTRY.md`
9. `REFERENCE_PROJECTS.md`

After that, read runtime code.
