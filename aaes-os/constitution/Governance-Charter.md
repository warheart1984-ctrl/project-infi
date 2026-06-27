# Governance Charter

**Version:** 1.0
**Status:** Foundational
**Date:** June 25, 2026

## Purpose

Defines governance bodies, roles, and decision authority for AAES-OS.

## Bodies

| Body | Mandate |
|------|---------|
| **Constitutional Council** | Oversees invariants, amendments, and governance evolution |
| **Architecture Review Board (ARB)** | Reviews all core architectural changes |
| **Security Council** | Oversees security invariants, threat models, and controls |
| **Stewardship Board** | Maintains institutional memory and continuity |

## Roles

- **Founders** — ultimate constitutional authority (temporary until v2.0)
- **Stewards** — maintain governance integrity
- **Contributors** — propose changes, submit ADRs, provide evidence
- **Reviewers** — validate proposals against governance principles

## Decision Authority

- Core changes require ARB + Constitutional Council approval.
- Security changes require Security Council approval.
- Amendments require constitutional process.

## Evaluation vs Adoption

> **Governance should determine how changes are evaluated, but evidence should determine whether changes are adopted.**

This rule separates **process** from **substance**:

| Domain | Role | Examples |
|--------|------|----------|
| **Governance** | Defines evaluation | Review bodies, checklists, ADR requirements, CTS gates, separation of powers, who may propose vs who may approve |
| **Evidence** | Determines adoption | Empirical data, stress tests, invariant proofs, receipts, simulations, replication results |

Governance bodies may reject a proposal for procedural or constitutional reasons before evidence is complete. They may not adopt a change on authority alone when evidence is insufficient, contradictory, or unreplicated.

Conversely, strong evidence does not bypass governance evaluation. Evidence answers *whether* a change should land; governance answers *how* that question is asked, by whom, and under what constraints.

## Operational Implications

1. **Pull requests** — governance checks (ADR present, invariant impact declared, CTS passing) are necessary but not sufficient for merge; adoption requires linked evidence artifacts.
2. **ADRs** — record the decision and alternatives; evidence records justify the chosen alternative.
3. **Amendments** — constitutional vote governs the amendment process; evidence governs the amendment content.
4. **Runtime** — CRK-1 enforces governance gates; receipts and CTS supply the evidence layer that validates adoption.
