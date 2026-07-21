# External Standards Mapping Layer

**Release family:** CRK-1 companion specification  
**Status:** Frozen  
**Purpose:** Map CIS Core and its companion ecosystem to relevant external standards families while preserving CIS terminology and governance.

---

## 1. Normative intent

This layer does not replace CIS Core.

It provides a durable mapping surface for:

- ISO
- NIST
- IEEE
- W3C
- IETF

The goal is interoperability, auditability, and standards traceability without vendor lock-in.

## 2. Mapping rule

Each external standards family should be mapped to:

- the CIS requirement or artifact it supports
- the rationale for the mapping
- the artifact type it informs
- the evidence or implementation concern it strengthens

## 3. Family mapping overview

| Family | Typical use in CIS ecosystem |
|-------|-----------------------------|
| ISO | Management systems, quality, governance, and process control |
| NIST | Risk, security, AI governance, and control baselines |
| IEEE | Ethics, agent behavior, and implementation guidance |
| W3C | Web data models, provenance, JSON-LD, and interoperability |
| IETF | Protocol norms, wire-format conventions, and interoperability rules |

## 4. Mapping expectations

- ISO mappings should support governance and management-system alignment.
- NIST mappings should support risk, control, and assurance alignment.
- IEEE mappings should support ethical and implementation guidance.
- W3C mappings should support semantic interoperability and provenance.
- IETF mappings should support protocol and encoding discipline.

## 5. Machine-readable registry

The machine-readable mapping registry lives in [EXTERNAL_STANDARDS_MAPPING.spec.json](./EXTERNAL_STANDARDS_MAPPING.spec.json).
