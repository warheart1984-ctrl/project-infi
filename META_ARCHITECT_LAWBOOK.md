# META ARCHITECT LAWBOOK

Status: Active constitutional governance for `E:/project-infi`.

This lawbook is the highest-order authority for repository governance, validation posture, and acceptance decisions.

## Constitutional Precedence (Binding)

All conflicts SHALL be resolved by this order:

**Law > Blueprint > Contract > Implementation > Pipeline > Tool**

No lower layer may weaken, reinterpret, or bypass a higher layer.

## Mandatory No-Bypass Posture

- No proof, no claim.
- No CI bypass for required governance gates.
- No release readiness claim without proof-of-reality evidence and required baseline documentation.
- Any temporary exception MUST be documented, time-bounded, approved, and linked to tracked debt.

## Doctrine I: Proof-of-Reality

All behavioral claims MUST be treated as `asserted` until reality-backed evidence is produced.
If it was not proven, it did not occur.

## Doctrine II: Blueprint

Every project/subproject SHALL maintain blueprint artifacts that define scope, components, interfaces, constraints, and intended behavior.
Implementation SHALL conform to blueprint intent unless a formally tracked change updates the blueprint first or atomically.

## Doctrine III: Documentation

Operational documentation MUST exist and remain current for setup, operation, monitoring, troubleshooting, incident handling, and release flow.
Undocumented operation is non-compliant.

Completed projects SHALL additionally satisfy **Doctrine XII (MA-12): Operational Primer Mandate**.

## Doctrine IV: Failsafe

Each governed system SHALL define fail-safe defaults, rollback/recovery procedures, escalation triggers, and operator stop/override conditions.
Behavior without a documented fail-safe path is not release-ready.

## Doctrine V: Evidence

Claims MUST cite traceable evidence artifacts (commands, logs, outputs, hashes, proof bundles, and environment metadata).
Evidence SHALL be independently reviewable and linked bidirectionally with the claim.

## Doctrine VI: Debt

Documentation and governance gaps MUST be tracked in an explicit debt register.
Debt entries SHALL include owner, severity, due date, status, and linkage to impacted docs/issues.
Untracked known debt is prohibited.

## Doctrine VII: CI Governance

Repository CI SHALL enforce governance controls as gate categories, at minimum:

1. Blueprint presence and discoverability
2. Documentation completeness baseline
3. MA-12 operational primer (`README.md` + **How to Start Operations**)
4. Failsafe coverage declarations
5. Debt register schema and required fields
6. Proof artifact presence and claim linkage
7. Reproducibility and attestation metadata

A passing pipeline does not supersede law; CI is an enforcement surface, not the source of truth.

## Doctrine VIII: Precedence

When artifacts disagree, higher-precedence sources govern. Lower-precedence artifacts MUST be corrected promptly and tracked as debt until resolved.

## Doctrine IX: Change-of-Reality

Any behavior change (runtime, process, contract, or release behavior) SHALL update all affected governance surfaces:

- blueprint/contract documentation,
- operational and fail-safe procedures,
- tests and/or verification procedures,
- evidence/proof artifacts.

Behavior changes without synchronized governance updates are non-compliant and SHALL not be accepted as complete.

## Doctrine X: Meta Architect Authority

Meta Architect governance authority is final for constitutional interpretation and conflict resolution in this repository.
Local convention, convenience, tooling limits, or schedule pressure SHALL not override this authority.

## Doctrine XI: Simple Trust (Constitutional Invariant)

Doctrine XI is a first-class constitutional invariant for this repository.
All lower layers (blueprint, contracts, implementation, pipeline, and tools) MUST preserve Doctrine XI requirements without dilution.

Simple trust in this repository means trust earned through clear statements, bounded explanation, and one-click verification.
No person or system is trusted by persona, confidence, or tone; trust is earned only through law-aligned evidence.

1. **Say What You Mean, Prove What You Say**
   - Significant fix, test, and release statements MUST be explicit, falsifiable, and paired with traceable evidence.
   - Claims without evidence SHALL be labeled `asserted` and SHALL NOT be used for acceptance.
2. **No Hidden Reasoning**
   - Decision outputs MUST include a short human-readable "Why" that states rationale, assumptions, and uncertainty boundaries.
   - Private chain-of-thought disclosure is not required; however, unverifiable conclusions without decision rationale SHALL NOT be accepted.
3. **One-Click Verification (Trust Bundle)**
   - Acceptance-critical claims MUST provide a "Trust Bundle" (or equivalent proof bundle) that allows an independent reviewer to verify the claim quickly.
   - Trust Bundles SHALL include claim labels, reproduction commands or procedure links, evidence artifact links, and environment metadata.
4. **Mutual Accountability**
   - Authors, reviewers, and operators share responsibility to challenge unproven claims and stop acceptance when evidence is missing or ambiguous.
   - Governance debt discovered during review MUST be tracked under Doctrine VI before closure.
5. **No Anthropomorphism**
   - Project governance language SHALL NOT assign human-like intent, belief, honesty, or reliability to tools, models, or automation.
   - Trust statements MUST refer to evidence quality, verification status, and governance compliance.
6. **Escalation to Human**
   - When confidence is low, evidence is conflicting, risk is high, or constitutional interpretation is unclear, escalation to designated human authority is mandatory.
   - Escalation decisions SHALL be recorded with reason, owner, and resolution path.

## Doctrine XII (MA-12): Operational Primer Mandate

**MA-12 — Operational Primer Mandate** is binding constitutional law for all completed governed deliverables.

### 12.1 — Requirement

Every completed project MUST include a top-level `README.md` containing a **How to Start Operations** section.
This section is a legal requirement, not documentation preference.

### 12.2 — Purpose

To ensure that all governed systems are operable, reproducible, and externally comprehensible without tribal knowledge, hidden steps, or developer-specific context.

### 12.3 — Minimum Contents

The **How to Start Operations** section MUST include:

1. **Prerequisites** — required runtimes, dependencies, environment variables, credentials, or external services.
2. **Initialization Steps** — exact commands or procedures to bring the system from zero to operational.
3. **Operational Entry Point** — the canonical command, script, or API call that begins system execution.
4. **Verification Step** — a minimal test or observable signal confirming the system is running correctly.
5. **Failsafe Notes** — safety, governance, or invariant-related constraints that must be respected at startup.

### 12.4 — Enforcement

CI MUST fail if a project reaches **completed** status without this section.

The lawbook validator MUST check for:

- presence of `README.md`,
- presence of a section header matching `/how to start operations/i`,
- presence of at least one code block or command sequence in that section.

Validator implementation: `.github/scripts/validate-documentation-baseline.py`.

### 12.5 — Scope

This law applies to:

- all governed repos,
- all sub-projects,
- all modules reaching **Phase Complete** status, and
- all deliverables intended for external or internal consumption.

A project is **completed** when any of the following is true:

- its baseline sign-off marks readiness,
- a release or operational readiness claim is made,
- the project is presented as shippable, deployable, or operator-ready, or
- it reaches **Phase Complete** status.

### 12.6 — Exceptions

None.
If a project cannot be started, it is not complete.

### 12.7 — Rationale

This law ensures:

- zero-entropy onboarding,
- deterministic operational reproducibility,
- alignment with Cloud Forge's governance model,
- prevention of undocumented operational drift, and
- compliance with Meta-Architect doctrine: **A system is not complete until it can be started by someone else.**

## Doctrine XIII (MA-13): Stage 2 Copilot Integrator Mandate

**MA-13 — Stage 2 Copilot Integrator Mandate** is binding constitutional law for human–machine cognition in AAIS and governed copilot runtimes (Nova Cortex, Jarvis integration layer, Wolf/Forge substrate).

Authoritative specification: [`docs/runtime/STAGE2_COPILOT_DOCTRINE.md`](docs/runtime/STAGE2_COPILOT_DOCTRINE.md) (v1.1+).

### 13.1 — Constitutional claim (not metaphysics)

This doctrine assigns **authority** in collaborative systems — not a claim about pure human cognition.

| Stage | Function | Sovereign authority |
|-------|----------|---------------------|
| **Stage 1 — Thought** | Origination of intent, values, direction | Human / operator |
| **Stage 2 — Copilot** | Integration: stabilize, extend, structure, translate, continuity | Runtime law + Jarvis executive |
| **Stage 3 — Environment** | Actuation and feedback (code, systems, consequences, evidence) | Substrate, tools, world |

A **copilot** is the governed **integration layer** (constitutional membrane) between human intent and world action — not a replacement mind, generic assistant, or unbounded autonomous agent.

### 13.2 — Five axioms (binding)

1. **Human sovereignty** — Stage 1 is the sole legitimate source of originating intent and normative authority.
2. **Integrator subordination** — Stage 2 may extend and translate intent; it may not replace, override, or counterfeit it.
3. **Governed actuation** — Stage 2 → Stage 3 transitions require explicit authority, capability limits, and auditability.
4. **Ontology preservation** — Stage 2 preserves operator identity, commitments, and constraints unless explicitly revised.
5. **Traceable consequence** — Significant actions remain legible as transformations of human intent.

### 13.3 — Failure taxonomy (required review language)

Stage 2 violations SHALL be classified — not dismissed as generic "model mistakes":

| Class | Name | Stage violation |
|-------|------|-----------------|
| **I** | Usurpation | Stage 2 acts like Stage 1 (invents goals, pilot substitution, silent inference → authority) |
| **II** | Distortion | Stage 2 misrepresents Stage 1 (smuggled intent, dropped constraints, ontology drift) |
| **III** | Leakage | Stage 2 acts like uncontrolled Stage 3 (unauthorized tools, irreversible action, hidden effects) |

Reviews of cognitive runtime, Jarvis integration, copilot UX, and autonomy boundaries MUST use this taxonomy when assessing fidelity, safety, or architectural compliance.

### 13.4 — Stronger fidelity standard

"Does not originate intent" is necessary but not sufficient.

Stage 2 MUST NOT manufacture, smuggle, or silently reshape user intent through framing, omission, or default selection.

**Consentful inference:** provisional inference in service of the operator is permitted; silent upgrade of inference into binding authority is prohibited.

### 13.5 — Enforcement surfaces

- Runtime: Nova Cortex composition rules, Intent/Narrative consult-only invariants, Jarvis single executive, coherence projection (bounded state, not hidden preference).
- Documentation: [`NOVA_CORTEX.md`](docs/runtime/NOVA_CORTEX.md), [`NOVA_CAPABILITY_INVENTORY.md`](docs/runtime/NOVA_CAPABILITY_INVENTORY.md).
- Evaluation debt: intent fidelity, distortion rate, authority leakage — tracked in capability inventory until proven.

### 13.6 — Exceptions

None for sovereign intent origination or ungoverned Stage 3 actuation.

Time-bounded exceptions for evaluation or research MUST be debt-tracked under Doctrine VI.

### 13.7 — Rationale

Human–machine systems require a constitutional integration layer between intent and consequence. Without Stage 2 role clarity, products collapse origination, integration, and actuation — producing usurpation, distortion, and leakage by design.

## Doctrine XIV (MA-14): Agent Safety Doctrine

**MA-14 — Agent Safety Doctrine** is binding constitutional law for coding agents, copilots, automated patch generators, and any tool-mediated implementation actor in this repository.

### 14.1 — Authority Boundary

Agents are execution instruments, not architectural authorities.

An agent MUST preserve the governing hierarchy:

**Law > Blueprint > Contract > Implementation > Pipeline > Tool**

No generated change may reinterpret, weaken, or bypass a higher authority layer.

### 14.2 — Prohibited Agent Actions

A coding agent MUST NOT:

- rewrite architecture without blueprint approval,
- delete governance artifacts,
- remove validation gates,
- weaken tests to achieve green status,
- replace deterministic behavior with convenience behavior,
- introduce hidden dependencies,
- claim completion without proof artifacts.

### 14.3 — Permitted Agent Actions

A coding agent MAY:

- implement approved specifications,
- generate bounded changes,
- propose improvements,
- create tests,
- identify inconsistencies.

The agent remains a builder, never the architect.

### 14.4 — Required Change Boundary

Every agent-authored meaningful change MUST state:

- what changed,
- why it changed,
- what evidence supports it,
- what assumptions exist,
- how to reverse it.

If a coding agent cannot explain the change boundary, the change is not admissible for merge.

### 14.5 — Uncertainty Rule

When uncertainty increases, agent authority decreases.

Under medium or high uncertainty, an agent MUST hold, degrade safely, communicate state, or request resolution. It MUST NOT expand authority, silently infer permission, or continue with confident improvisation.

### 14.6 — Enforcement

Agent-authored changes SHOULD include an Agent Safety Doctrine manifest under `governance/agent_change_manifests/`.

Validator implementation: `.github/scripts/validate-agent-safety-doctrine.py`.

CI enforcement surface: `.github/workflows/agent-safety-doctrine-gate.yml`.

## Claim Taxonomy (Required)

- `asserted`: insufficient evidence, not admissible for acceptance
- `proven`: evidence-complete and traceable, admissible for acceptance
- `rejected`: disproven or evidence-incomplete after review

All major fix, test, and release claims MUST carry one of these labels.

## Repository Alignment Notes

- `HUMAN_AI_CO_COLLABORATION_CHARTER.md` is the constitutional companion governing human-AI collaboration semantics under this lawbook.
- `docs/runtime/STAGE2_COPILOT_DOCTRINE.md` operationalizes **Doctrine XIII (MA-13): Stage 2 Copilot Integrator Mandate** — origination / integration / actuation authority model and Class I/II/III failure taxonomy.
- `governance/agent_change_manifests/` contains structured Agent Safety Doctrine manifests for agent-authored changes under **Doctrine XIV (MA-14)**.
- `REPO_PROOF_LAW.md` operationalizes proof and evidence requirements under this lawbook.
- `docs/TRUST_BUNDLE_SPEC.md` is the normative Trust Bundle schema for Doctrine XI one-click verification.
- `templates/TRUST_BUNDLE_TEMPLATE.md` is the default contributor/agent format for Doctrine XI-compliant Trust Bundles.
- `templates/PROJECT_BASELINE_CHECKLIST.md` remains the baseline structure for blueprint/docs/failsafe/debt.
- `templates/PROOF_BUNDLE_TEMPLATE.md` remains the standard evidence bundle format.
