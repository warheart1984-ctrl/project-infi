# CIS Conformance Requirements

**Release family:** CRK-1 companion specification  
**Status:** Frozen  
**Purpose:** Formal conformance requirement set for CIS Core, companion specifications, and implementation profiles.

---

## 1. Conformance statement

A system conforms to CIS only if it preserves the constitutional core, implements the required governance process, and exposes evidence sufficient for independent implementation and review.

## 2. Required criteria

| Criterion | Requirement | Verification expectation |
|----------|-------------|--------------------------|
| CR-1 | CIS Core must remain the single authoritative constitutional specification | The hierarchy and release docs identify CIS Core as the normative source of truth |
| CR-2 | Companion specifications must inherit Core terminology | Companion docs do not redefine constitutional terms |
| CR-3 | The governance process must be part of the spec surface | The specification includes document status, stewardship, versioning, traceability, and release lifecycle |
| CR-4 | The ecosystem must support longevity and independent implementability | A new implementer can build a conforming implementation without founder dependency |
| CR-5 | The ecosystem must remain model-agnostic | The platform can route across compatible reasoning engines without changing the core |
| CR-6 | Evidence must precede claims of conformance | Claims are backed by proof surfaces, receipts, and validation artifacts |
| CR-7 | Conformance must be traceable | Each requirement maps to a component, evidence, and test |
| CR-8 | Research OS must preserve continuous improvement artifacts | Evidence, Insights, Ideas, and Actions remain durable and reviewable |
| CR-9 | Major artifacts must follow the shared governance model | Each major artifact publishes document status, version, steward, classification, parent specification, traceability, CCP / CCR history, and release history |

## 3. No founder dependency criterion

Conforming implementations must not require:

- private explanation from the original authors
- unpublished conventions
- hidden implementation knowledge
- non-reproducible operator procedures

Independent implementers must be able to:

- inspect the published specifications
- derive the expected behavior
- run the published conformance checks
- evolve the system through governed change control

## 4. Governance process requirement

The governance process itself is a spec surface and must be documented as such.

At minimum, the specification must expose:

- document status lifecycle
- stewardship and release authority
- versioning and baseline rules
- traceability from requirement to evidence
- release and freeze transitions
- conformance review and approval path

## 5. Acceptance evidence

Acceptable evidence may include:

- release docs
- machine-readable spec files
- conformance inputs
- proof-surface publication
- validation and test results
- replayable records
