# CIS Conformance Suite Generation

**Release family:** CRK-1 companion specification  
**Status:** Frozen  
**Purpose:** Define the generation path for the CIS conformance suite from the traceability matrix source of truth.

---

## 1. Source of truth

The conformance suite specification and conformance suite input are generated from the CIS standards hierarchy traceability matrix.

That means the following artifacts should remain in sync:

- `CIS_STANDARDS_HIERARCHY.spec.json`
- `CIS_STANDARDS_TRACEABILITY_MATRIX.md`
- `CIS_CONFORMANCE_SUITE_SPECIFICATION.md`
- `CIS_CONFORMANCE_SUITE_INPUT.spec.json`

## 2. Generation rule

Do not hand-maintain the conformance suite input when the traceability matrix changes.

Instead:

1. Load the hierarchy source.
2. Read the traceability matrix rows.
3. Derive the conformance-suite cases, traceability path, validation families, and acceptance criteria.
4. Serialize the generated suite input.
5. Verify the serialized output matches the committed release artifact and the suite specification.

## 3. Machine-readable generator

The generator lives in [CIS_CONFORMANCE_SUITE_INPUT.spec.json](./CIS_CONFORMANCE_SUITE_INPUT.spec.json) and the workspace loader in `tools/cis-conformance.ts`.
