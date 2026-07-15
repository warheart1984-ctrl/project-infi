# SOCK Alignment Specification

**Release family:** CRK-1 companion specification  
**Status:** Frozen  
**Depends on:** CIS Core v1.0 and the Sovereign OS Constitutional Kernel (SOCK) Specification  
**Stewardship:** CIS release maintainers  
**Constitutional sections:** 1-6  
**Informative sections:** 7

---

## 1. Purpose

This specification defines how CIS Core aligns with the Sovereign OS Constitutional Kernel (SOCK) without redefining either constitutional layer.

It exists to make the bridge between CIS obligations and SOCK runtime semantics explicit and traceable.

SOCK alignment SHALL remain a single-responsibility companion specification for bridge semantics and traceability.
SOCK alignment is part of the frozen companion baseline for CIS Core v1.0.

## 2. Constitutional rule

SOCK alignment SHALL preserve the following rule:

- CIS Core defines obligations.
- SOCK implements constitutional execution semantics.
- No alignment document SHALL redefine CIS Core or SOCK requirements.

## 3. Alignment target

The SOCK specification defines the following core languages:

- CSL: Constitutional Schema Layer
- ISL: Intent Specification Layer
- CIC: Constitutional Inference Contract
- CCC: Constitutional Continuity Contract
- COE: Constitutional Operating Environment

SOCK alignment SHALL map CIS requirements to these runtime-facing constitutional surfaces where applicable.

The alignment target SHALL be descriptive and traceable rather than prescriptive of implementation detail.

## 4. Alignment matrix

The alignment matrix SHALL be able to answer:

- Which CIS requirement is being realized?
- Which SOCK language carries the execution responsibility?
- Which evidence surface proves the alignment?
- Which release artifact records the mapping?

Each aligned mapping SHOULD be traceable through the Standards Traceability Matrix and the release evidence package.

## 5. Boundary rule

SOCK alignment SHALL NOT:

- introduce new CIS obligations
- weaken the frozen CIS baseline
- reinterpret trust, governance, or continuity terminology
- hide runtime behavior behind untraceable implementation detail

## 6. Conformance

A conforming SOCK alignment artifact SHALL:

- preserve traceability to CIS Core
- preserve traceability to the SOCK specification
- make runtime surface mapping explicit
- support evidence-based review of the bridge between constitution and execution

Conformance SHALL verify that the alignment document does not introduce new CIS obligations.

## 7. Informative note

The existing SOCK documentation in the docs/specifications and docs/runtime surfaces is the implementation-side reference for this alignment work.
