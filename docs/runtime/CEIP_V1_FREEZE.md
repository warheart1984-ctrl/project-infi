# CEIP v1.0 Freeze Notice

Effective 14 July 2026, CEIP v1.0 is the frozen constitutional integration contract and reference runtime for the 19-stage lifecycle.

The freeze covers stage identity and order, canonical workflow/event/transition/object contracts, the human-approval boundary, receipt/replay/conformance ordering, knowledge-admission boundary, UGR promotion rule, and terminal audit requirement. Machine-readable artifact hashes are recorded in [`packages/ceip-runtime/ceip.freeze.json`](../../packages/ceip-runtime/ceip.freeze.json).

## Change control

- Constitutional meaning or invariant changes require constitutional review.
- Contract additions within 1.x must be backward compatible and optional for existing consumers.
- Breaking schema, event, state, ordering, or behavioral changes require a new major version.
- Runtime implementation changes must continue passing the pinned CEIP v1 conformance suite.
- New capabilities integrate as adapters or extensions and may not create a second execution path.
- Event changes require a version, migration/upcaster, compatibility tests, and replay evidence.
- A freeze manifest update without its required review evidence is not authorization to change the contract.

This freeze does not declare production readiness. CEIP remains a validated reference baseline until PC-1 acceptance evidence is complete.

Compatible external artifacts may be added without changing frozen bytes. Current companions include the [Constitutional Hierarchy](./CONSTITUTIONAL_HIERARCHY.md), [CEIP Enterprise Intelligence Profile](./CEIP_ENTERPRISE_PROFILE_V1.md), and [CCS Independence Requirements](./CCS_INDEPENDENCE_REQUIREMENTS.md).
