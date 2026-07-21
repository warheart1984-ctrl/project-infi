# CIS Standards Traceability Matrix

**Release family:** CRK-1 companion specification  
**Status:** Frozen  
**Purpose:** Formal traceability matrix for CIS Core, companion specifications, implementation profiles, evidence, replay, and external standards mapping.

---

## 1. End-to-end constitutional trace

Every CIS Core requirement SHALL trace through the same constitutional path:

`Architecture -> Ontology -> Knowledge Graph -> GKS -> Research OS -> Reference Runtime -> Conformance -> Evidence -> Replay -> External Standards`

That path ensures every requirement has a single constitutional interpretation, a single implementation surface, a single verification surface, and a single evidence surface.

| Layer | Constitutional responsibility | Required artifact or surface | Verification role |
|---|---|---|---|
| CIS Core requirement | Defines the normative obligation | CIS Core requirement identifier and text | Source of truth |
| Architecture | Decomposes the obligation into system structure and interfaces | Reference Architecture | Structural trace |
| Ontology | Normalizes canonical terms and relationships | Ontology | Semantic trace |
| Knowledge Graph | Encodes governed relationships between concepts and artifacts | Knowledge Graph specification and graph entities | Relationship trace |
| GKS | Governs canonical knowledge admission, authorization, canonical state, and supersession | Governed Knowledge Store Specification and canonical object records | Operational knowledge trace |
| Research OS | Preserves evidence, insights, ideas, and actions as durable institutional memory | Research OS Specification and research objects | Stewarded improvement trace |
| Reference Runtime | Executes the governed behavior required by the constitutional layer | Reference Runtime specification and runtime logs | Execution trace |
| Conformance | Verifies that the implementation satisfies the frozen constitutional baseline | Conformance Suite and conformance report | Compliance trace |
| Evidence | Records objective proof of the trace and its outcomes | Evidence package, receipts, hashes, and review records | Audit trace |
| Replay | Reconstructs the governed history deterministically | Replay path and replay artifact | Independent verification trace |
| External Standards | Maps CIS obligations to ISO, NIST, IEEE, W3C, and IETF families | External standards mapping documents and registry | Interoperability trace |

## 2. Requirement matrix

The following matrix applies to every CIS Core requirement.

| Requirement family | Architecture | Ontology | Knowledge Graph | GKS | Research OS | Reference Runtime | Conformance | Evidence | Replay | External Standards |
|---|---|---|---|---|---|---|---|---|---|---|
| Every CIS requirement | SHALL be decomposed into a bounded system responsibility | SHALL be represented by a canonical term or relation | SHALL be encoded as a governed relationship set | SHALL be admitted, authorized, and superseded through canonical state | SHALL be preserved as evidence, insights, ideas, and actions | SHALL be implemented in executable behavior | SHALL be validated against the frozen baseline | SHALL produce objective proof artifacts | SHALL be replayable without private explanation | SHALL identify the corresponding external standard family or intentional extension |

## 3. Matrix rows

| Requirement | Component | Evidence | Test |
|---|---|---|---|
| CIS Core remains the single authoritative constitutional specification | `CIS_STANDARDS_HIERARCHY.md` and `CIS_STANDARDS_HIERARCHY.spec.json` | Hierarchy doc, machine-readable hierarchy spec, release index | `packages/aaes-governance/src/proofSurface.test.ts` registry publication coverage |
| Companion specifications inherit Core terminology rather than redefining it | `CIS_STANDARDS_HIERARCHY.md` | Normative rule section and companion specification list | `packages/aaes-governance/src/proofSurface.test.ts` proof-surface summary coverage |
| Every artifact carries consistent governance status, stewardship, versioning, traceability, and release lifecycle fields | `ARTIFACT_GOVERNANCE_MODEL.md` and `ARTIFACT_GOVERNANCE_REGISTRY.spec.json` | Artifact governance model and registry | `tests/release/artifact-governance.test.ts` |
| Implementation profiles adapt CIS for domain-specific constraints without changing constitutional requirements | `CIS_STANDARDS_HIERARCHY.md` | Implementation profile section and domain list | `docs/crk1/release/CIS_STANDARDS_HIERARCHY.spec.json` ingest compatibility |
| Standards traceability answers requirement, component, evidence, replay, receipt, and test for each capability | `CIS_STANDARDS_TRACEABILITY_MATRIX.md` and `CIS_CONFORMANCE_SUITE_SPECIFICATION.md` | Traceability matrix section, formal matrix rows, and proof-chain mapping | `docs/crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md` review and downstream conformance mapping |
| Research OS preserves evidence, insights, ideas, and actions as durable institutional memory | `RESEARCH_OS_SPECIFICATION.md` | Research OS section and object flow | `packages/aaes-governance/src/proofSurface.test.ts` evidence-surface publication |
| GKS preserves governed knowledge admission, canonical state, replay, trust, and supersession | `GOVERNED_KNOWLEDGE_STORE_SPECIFICATION.md` | Canonical object model and admission lifecycle | `tests/release/artifact-governance.test.ts` governed knowledge checks |
| The conformance suite validates constitutional, replay, receipt, trust, and acceptance criteria | `CIS_CONFORMANCE_SUITE_SPECIFICATION.md` and `CIS_CONFORMANCE_SUITE_INPUT.spec.json` | Suite specification, validation families, and generated input | `tests/release/cis-conformance-generation.test.ts` and suite execution coverage |
| Launch readiness is governed by evidence rather than subjective judgment | `CIS_LAUNCH_READINESS_SPECIFICATION.md` | Promotion gates and release evidence bundle | `tests/release/launch-readiness.test.ts` release evidence coverage |
| CORI Alpha is the first independently verifiable constitutional proof | `CORI_ALPHA_PROOF_CHAIN.md` | Proof chain, evidence package, constitutional receipt, and replay path | `tests/release/cori-alpha-proof.test.ts` replay, receipt, and conformance coverage |
| The hierarchy is available as machine-readable ingest input | `CIS_STANDARDS_HIERARCHY.spec.json` | JSON hierarchy artifact | Orchestrator or importer can parse the JSON document directly |
| External standards families are mapped for interoperability and traceability | `EXTERNAL_STANDARDS_MAPPING.md` and `EXTERNAL_STANDARDS_MAPPING.spec.json` | External mapping layer and registry | `tests/release/external-standards.test.ts` |
| The conformance suite is generated from the traceability matrix source of truth | `CIS_CONFORMANCE_SUITE_GENERATION.md`, `CIS_CONFORMANCE_SUITE_INPUT.spec.generator.json`, and `CIS_CONFORMANCE_SUITE_INPUT.spec.json` | Generation rule, generator record, generated input, traceability path, validation families, and acceptance criteria | `tests/release/cis-conformance-generation.test.ts` |

## 4. Companion specification completion matrix

| Companion spec | Constitutional responsibility | Evidence surface | Review surface |
|---|---|---|---|
| Governed Knowledge Store Specification | Governed knowledge admission, replay, and trust lifecycle | `GOVERNED_KNOWLEDGE_STORE_SPECIFICATION.md` | Release bundle review |
| CIS Conformance Suite Specification | Constitutional verification, replay validation, receipt validation, trust validation, and acceptance criteria | `CIS_CONFORMANCE_SUITE_SPECIFICATION.md` | Release bundle review |
| CIS Launch Readiness Specification | Evidence-governed release lifecycle | `CIS_LAUNCH_READINESS_SPECIFICATION.md` | Release bundle review |
| Research OS Specification | Evidence -> Insights -> Ideas -> Actions workflow | `RESEARCH_OS_SPECIFICATION.md` | Release bundle review |
| SOCK Alignment Specification | Bridge CIS obligations to SOCK runtime semantics | `SOCK_ALIGNMENT_SPECIFICATION.md` | Release bundle review |
| CORI Alpha Proof Chain | Minimum governed proof workflow for constitutional evidence | `CORI_ALPHA_PROOF_CHAIN.md` | Release bundle review |

## 5. Notes

- The matrix is intentionally bounded to the constitutional layer and its companion artifacts.
- Domain profiles may add sector-specific evidence, but they may not change the constitutional requirements listed here.
- The traceability matrix is a companion specification and inherits CIS Core terminology.
- The generated conformance-suite input lives in [CIS_CONFORMANCE_SUITE_INPUT.spec.json](./CIS_CONFORMANCE_SUITE_INPUT.spec.json).
- That input carries the traceability path, validation families, and acceptance criteria used to prove CORI Alpha end to end.
- The conformance suite specification, generator, and generated input are intended to remain in sync with this matrix.
- The companion specification completion matrix records the newer companion surfaces that extend the frozen baseline without redefining it.
