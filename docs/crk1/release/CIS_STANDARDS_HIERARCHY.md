# CIS Standards Hierarchy and Research OS Mapping

**Release family:** CRK-1 companion specification  
**Status:** Frozen  
**Purpose:** Define the constitutional standards hierarchy for CIS Core, companion specifications, implementation profiles, and the permanent Research OS.

This artifact is part of the frozen CIS Core v1.0 constitutional baseline.

---

## 1. Normative model

The standards ecosystem is organized as a stable constitutional core with companion specifications that inherit, rather than redefine, core terminology.

### Normative rule

- CIS Core is the single authoritative constitutional specification.
- Companion specifications may specialize behavior, structure, and implementation.
- Companion specifications may not redefine core terms.
- Companion specifications may not weaken constitutional requirements.

## 2. Specification layers

| Layer | Role | Rule |
|------|------|------|
| CIS Core | Normative source of truth | Defines all constitutional terms and requirements |
| Companion specifications | One responsibility each | Inherit Core terminology and extend only their own domain |
| Implementation profiles | Domain adaptation | Apply Core requirements to a sector or deployment class |
| Implementation profile freeze criteria | Freeze gate | Defines when a `profile-*` artifact may graduate from Draft to Frozen |
| Reference Runtime | Execution and validation | Proves the specification can run |
| Conformance Suite | Verification | Proves the implementation matches the spec |
| Standards Traceability Matrix | Evidence map | Connects requirement, component, evidence, and test |
| Research OS | Institutional memory | Captures evidence, insights, ideas, and actions |

## 3. Companion specification set

Each companion specification has exactly one primary responsibility.
The companion specification set below is part of the frozen companion baseline for CIS Core v1.0.

| Companion specification | Responsibility |
|------------------------|----------------|
| Reference Architecture | System decomposition and boundaries |
| Ontology | Shared semantic contract |
| Knowledge Graph Specification | Operational knowledge and continuity structure |
| Governed Knowledge Store Specification | Canonical knowledge admission, replay, and trust lifecycle |
| Conformance Suite | Validation and compliance testing |
| Reference Runtime | Executable proof of the architecture |
| Standards Traceability Matrix | Requirement-to-evidence, receipt, and replay mapping |
| Implementation Profiles | Domain adaptation without constitutional drift |
| DX Guide | Developer onboarding and implementation guidance |
| Documentation Specification Family | Authoring, filing, and release rules |
| Launch Readiness Specification | Evidence-governed release lifecycle |
| Research OS | Evidence, insights, ideas, and actions workflow |
| SOCK Alignment Specification | Bridge CIS obligations to SOCK runtime semantics |
| CORI Alpha Proof Chain | Minimum governed proof workflow for constitutional evidence |

## 4. Governance model

Every artifact in the ecosystem should carry the same governance fields.

### Document status lifecycle

`Draft -> Technical Review -> Baseline Candidate -> Constitutional Approval -> Frozen -> Published`

### Governance fields

| Field | Meaning |
|------|---------|
| Document Status | Current lifecycle stage |
| CCP / CCR | Constitutional change governance and constitutional change request record |
| Stewardship | Named owner or stewardship group |
| Versioning | Stable semantic version or release ID |
| Traceability | Links to requirement, evidence, and tests |
| Release lifecycle | How the document moves between stages |

## 5. Core principles

The formal principle draft lives in [CIS_CORE_PRINCIPLES.md](./CIS_CORE_PRINCIPLES.md).

The highest-priority principle for this slice is:

- Longevity and independent implementability

That principle means a conforming implementation must be buildable and governable by an implementer who has no founder dependency.

## 6. Conformance requirements

The formal conformance requirement set lives in [CIS_CONFORMANCE_REQUIREMENTS.md](./CIS_CONFORMANCE_REQUIREMENTS.md).

The no-founder-dependency criterion is mandatory for conformance:

- no private explanation from the original authors
- no unpublished conventions
- no hidden implementation knowledge
- no non-reproducible operator procedures

## 7. Inheritance rule

All companion specifications inherit CIS Core vocabulary.

That means:

- no duplicate definitions of constitutional terms
- no conflicting lifecycle semantics
- no local redefinition of evidence, governance, or compliance
- no divergence in traceability vocabulary

If a companion needs a specialized term, it must define it as a profile-specific extension, not a replacement for Core terminology.

## 8. Governance process as spec surface

The governance process itself is part of the specification surface.

That means the spec must describe:

- document status lifecycle
- stewardship and release authority
- versioning and baseline rules
- traceability from requirement to evidence
- release and freeze transitions
- conformance review and approval path

## 9. Standards traceability matrix

The formal traceability matrix lives in [CIS_STANDARDS_TRACEABILITY_MATRIX.md](./CIS_STANDARDS_TRACEABILITY_MATRIX.md).

The matrix answers four questions for each major capability:

1. Which constitutional requirement does this implement?
2. What architectural component realizes that requirement?
3. What evidence demonstrates conformance?
4. Which tests verify it?

The machine-readable ingest form lives in [CIS_STANDARDS_HIERARCHY.spec.json](./CIS_STANDARDS_HIERARCHY.spec.json).

## 10. Implementation profiles

Implementation profiles adapt CIS for a domain while preserving the constitution.
They remain active adaptation surfaces rather than frozen companion baselines.

Implementation profile freeze criteria define the objective gate for promoting a profile artifact to a frozen companion baseline.
The Government and Research profiles are the two worked examples of that process.

### Implementation profile status summary

| Profile family member | Status | Role in the release surface |
|---|---|---|
| Government | Frozen | Contrasting worked example for public-sector adaptation |
| Research | Frozen | Worked example for evidence-rich research adaptation |
| Healthcare | Draft | Active adaptation surface awaiting profile-specific evidence |
| Finance | Draft | Active adaptation surface awaiting profile-specific evidence |
| Education | Draft | Active adaptation surface awaiting profile-specific evidence |
| Infrastructure | Draft | Active adaptation surface awaiting profile-specific evidence |
| Regenerative Intelligence | Draft | Active adaptation surface awaiting profile-specific evidence |

### Worked-example policy

The implementation profile family SHALL keep two frozen worked examples for now:

- `profile-government`
- `profile-research`

Additional `profile-*` artifacts, including `profile-finance`, SHALL remain Draft until they satisfy the Implementation Profile Freeze Criteria and have a completed evidence package.

| Profile | Typical constraints |
|--------|---------------------|
| Government | retention, procurement, audit, and access controls |
| Healthcare | privacy, traceability, and evidence preservation |
| Finance | approvals, controls, and tamper-evident records |
| Research | reproducibility, citations, and experiment lineage |
| Education | transparency, explainability, and accessibility |
| Infrastructure | reliability, failover, and operational control |
| Regenerative Intelligence | continuity, stewardship, and feedback loops |

## 11. Research OS

Research OS is a permanent part of the ecosystem.

It captures research as four durable object types:

- Evidence
- Insights
- Ideas
- Actions

### Research OS responsibilities

- preserve institutional memory
- connect research to the standards hierarchy
- surface reusable evidence
- turn research into operational actions
- keep the constitution stable while learning accumulates

### Research OS outputs

| Output | Purpose |
|-------|---------|
| Evidence | Verifiable supporting material |
| Insights | Structured findings from analysis |
| Ideas | Candidate improvements or hypotheses |
| Actions | Concrete next steps with owners |

## 12. Governed Knowledge Store Specification

GKS is the operational knowledge layer of the ecosystem.

It preserves:

- sources
- observations
- canonical objects
- admission lifecycle
- validation
- authorization
- canonical state
- supersession

GKS extends Bradley's operational model with constitutional receipts, replay, trust ledger integration, conformance, standards traceability, and stewardship.

## 13. Launch Readiness Specification

The launch readiness specification governs release states and evidence.

It ensures each release can demonstrate conformance to the frozen constitutional baseline before publication.

## 14. SOCK Alignment Specification

SOCK alignment is a frozen companion baseline that documents how CIS obligations map into the constitutional execution semantics of the Sovereign OS Constitutional Kernel.

It preserves the boundary between constitutional obligations and runtime execution.

## 15. CORI Alpha Proof Chain

CORI Alpha is the first governed proof milestone for the ecosystem.

It requires a replayable chain covering:

- identity
- evidence
- provenance
- trust
- relationships
- constitutional decision
- constitutional receipt
- replay
- conformance
- evidence package

The proof package SHALL include the constitutional receipt, replay artifact or replay path, and conformance result needed for independent verification.

## 16. Companion registry

The companion-spec registry lives in [CIS_COMPANION_SPEC_REGISTRY.spec.json](./CIS_COMPANION_SPEC_REGISTRY.spec.json).

It publishes CIS Core, companion specifications, implementation profiles, Research OS, and the newer governed companion surfaces through the same proof-surface pattern.

## 17. Artifact governance model

The shared governance model lives in [ARTIFACT_GOVERNANCE_MODEL.md](./ARTIFACT_GOVERNANCE_MODEL.md) and [ARTIFACT_GOVERNANCE_REGISTRY.spec.json](./ARTIFACT_GOVERNANCE_REGISTRY.spec.json).

Every major artifact should carry the same metadata fields:

- Document Status
- Version
- Owner / Steward
- Normative or Informative classification
- Parent Specification
- Traceability Links
- CCP / CCR History
- Release History

## 18. External standards mapping

The external standards mapping layer is a frozen companion baseline and lives in [EXTERNAL_STANDARDS_MAPPING.md](./EXTERNAL_STANDARDS_MAPPING.md), [EXTERNAL_STANDARDS_MAPPING.spec.json](./EXTERNAL_STANDARDS_MAPPING.spec.json), and [EXTERNAL_STANDARDS_MAPPING_FREEZE.md](./EXTERNAL_STANDARDS_MAPPING_FREEZE.md).

It connects CIS artifacts to relevant ISO, NIST, IEEE, W3C, and IETF families without changing CIS terminology.

## 19. Conformance suite generation

The conformance suite generation layer lives in [CIS_CONFORMANCE_SUITE_SPECIFICATION.md](./CIS_CONFORMANCE_SUITE_SPECIFICATION.md), [CIS_CONFORMANCE_SUITE_GENERATION.md](./CIS_CONFORMANCE_SUITE_GENERATION.md), and the generator input record in [CIS_CONFORMANCE_SUITE_INPUT.spec.generator.json](./CIS_CONFORMANCE_SUITE_INPUT.spec.generator.json).

The generated conformance suite input must be derived from the traceability matrix source of truth.

## 20. Release governance

Before a companion spec becomes published:

- the core terminology must be stable
- the doc status must advance through governance
- the traceability matrix must include requirements, evidence, and tests
- the governance process must be present in the spec surface
- the implementation profile boundaries must be explicit
- the implementation profile freeze criteria must be satisfied
- the Research OS link must be declared if the spec consumes research output

Implementation profile instances remain Draft while they are serving as active adaptation surfaces.
They should receive a formal freeze notice only after the profile-specific evidence bundle, traceability surface, and governed release record are complete.

## 21. Ecosystem summary

This hierarchy keeps the constitutional layer stable while allowing:

- architecture to evolve
- runtime behavior to evolve
- profiles to adapt by domain
- documentation to grow
- research to accumulate
- governed companion completion to proceed without redefining CIS Core

The result is a standards ecosystem, not a single static spec.

The companion traceability matrix and machine-readable spec are part of the same release surface and should be treated as first-class evidence.
