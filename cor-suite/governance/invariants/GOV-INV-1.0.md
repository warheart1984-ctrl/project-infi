# GOV-INV-1.0 — AAES-OS Constitutional Invariants

**Version:** 1.0  
**Authority:** Governance Engine · COR Suite  
**Status:** Normative

These invariants are enforced by the governance engine and referenced in governance receipts (`invariantsEnforced[]`).

---

## 1. Deterministic Canonical State

Every canonical artifact **MUST** be registered in CAR-1.0.

- No artifact may exist in the repo without a CAR entry.
- Hashes **MUST** match content.
- No duplicate IDs or conflicting lifecycle states.

**Enforcement:** CAV-1.0 blocking findings; `INV-COR-PURE`.

---

## 2. Complete Provenance Chains

Every requirement **MUST** have at least one specification.

Every specification **MUST** have at least one implementation.

Every implementation **MUST** have at least one verification.

Every verification **MUST** reference evidence or test results.

No broken edges in PGI-1.0.

**Enforcement:** COR structural integrity; PGI edge completeness; `INV-LINEAGE`, `INV-STRUCTURAL`.

---

## 3. No Critical Verification Gaps

Requirements marked **critical** **MUST** have passing verification.

Missing or failing verification for critical requirements is **blocking**.

**Enforcement:** Proof Analysis critical claims; DRA `verificationGaps`; `INV-PROOF-CRITICAL`.

---

## 4. No Deprecated Dependencies Without Successors

Deprecated artifacts **MUST** declare `supersededBy`.

Requirements depending on deprecated artifacts **MUST** be flagged.

**Enforcement:** CAV advisory `deprecated_without_successor`; DRA `deprecatedDependencies`.

---

## 5. Governance Receipts MUST Be Canonical

Every governance decision **MUST** produce a signed receipt.

Receipts **MUST** be registered in CAR-1.0 (when receipt registration is enabled).

Unsigned receipts are invalid.

**Enforcement:** Governance engine signature field; CAR `governance_receipt` kind.

---

## 6. Measurement MUST Be Reproducible

COR-1.0, CSR-1.0, and DRA-1.0 **MUST** be deterministic given a fixed CAR snapshot.

PGI-1.0 **MUST** be stable under repeated runs with unchanged CAR.

**Enforcement:** Repo hygiene `deterministicArtifacts`; repeated pipeline runs in CI.

---

## 7. No Release With Blocking Findings

Any CAV-1.0 blocking finding **MUST** halt release.

Governance **MAY NOT** override validation.

**Enforcement:** CAV gate before COR; Constitutional Governance Pipeline; `ci-gate`.

---

## Mapping to engine invariant IDs

| GOV-INV | Engine ID |
|---------|-----------|
| §1, §7 | CAV validation, `INV-COR-PURE` |
| §2 | `INV-LINEAGE`, `INV-STRUCTURAL` |
| §3 | `INV-PROOF-CRITICAL` |
| §4 | CAV advisory + DRA scoring |
| §5 | Governance receipt signature |
| §6 | Hygiene + deterministic outputs |
| §7 | CI gate, reject/freeze decisions |
