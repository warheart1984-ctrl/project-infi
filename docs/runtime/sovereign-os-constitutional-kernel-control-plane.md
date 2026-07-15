# Sovereign OS Constitutional Kernel Control Plane Summary

This page maps the five SOCK languages to the runtime surfaces surfaced through the docs hub.
It is the operator-facing companion to the constitutional kernel specification.

## Runtime surface map

| SOCK layer | Constitutional role | Docs hub runtime surfaces | Evidence and governance surfaces |
| --- | --- | --- | --- |
| CSL | Defines constitutional state and evolution | [Sovereign OS Constitutional Kernel (SOCK) Specification](../specifications/aaes-os-constitutional-kernel-specification.md), [AAES-OS Specifications](../specifications/README.md) | [CIS Standards Traceability Matrix](../crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md), [Constitutional Release Record Template](../release/constitutional-release-record-template.md) |
| ISL | Defines governed requests and authority bindings | [AAES-OS Control Plane Specification](../specifications/aaes-os-control-plane-specification.md), [Sovereign IDE Runtime Surface](./sovereign-ide.md) | [Constitutional Release Record Template](../release/constitutional-release-record-template.md), [Launch Readiness Specification](../release/launch-readiness-specification.md) |
| CIC | Defines inference, bindings, and semantic reasoning | [AAES-OS Governance Specification](../specifications/aaes-os-governance-specification.md), [Sovereign IDE Runtime Surface](./sovereign-ide.md), [Constitutional Debugger](./Constitutional_Debugger.md) | [CIS Standards Traceability Matrix](../crk1/release/CIS_STANDARDS_TRACEABILITY_MATRIX.md), [Constitutional Release Receipt](../release/constitutional-release-receipt.md) |
| CCC | Defines continuity, lineage, and replay across time | [AAES-OS Constitutional Continuity Specification](../specifications/aaes-os-constitutional-continuity-specification.md), [Constitutional Execution Trace 1](./Constitutional_Execution_Trace_1.md), [Law of Laws Ledger](./Law_Of_Laws_Ledger.md) | [Launch Readiness Specification](../release/launch-readiness-specification.md), [ULX Merge Readiness Record](../release/ulx-merge-readiness-record.md) |
| COE | Defines governed execution, routing, scheduling, and promotion | [AAES-OS Control Plane Specification](../specifications/aaes-os-control-plane-specification.md), [Sovereign IDE Runtime Surface](./sovereign-ide.md), [Enforcement First Architecture](./Enforcement_First_Architecture.md), [CEN Enforcement Kernel](./CEN_Enforcement_Kernel.md) | [Constitutional Release Record Template](../release/constitutional-release-record-template.md), [Constitutional Release Receipt](../release/constitutional-release-receipt.md) |

## Docs hub interpretation

The docs hub exposes SOCK through three operator lenses:

1. The constitutional specification layer, where the five languages are defined.
2. The runtime surface layer, where those languages are mapped to operator-facing docs.
3. The release layer, where the same constitutional ideas are represented as governed artifacts.

## Operator rule

No runtime surface MAY redefine the five SOCK languages.
Runtime pages MAY describe implementation surfaces, but they MUST trace back to the canonical specification and traceability matrix.

## Navigation

- [Docs Hub](../README.md)
- [SOCK Specification](../specifications/aaes-os-constitutional-kernel-specification.md)
- [SOCK JSON Schema](../specifications/aaes-os-constitutional-kernel.schema.json)
- [AAES-OS Specifications Index](../specifications/README.md)

