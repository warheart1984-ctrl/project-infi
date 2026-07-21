# CCS Independence Requirements

An implementation-independent CCS must:

1. Consume only published standards, specifications, schemas, fixtures, and protocols.
2. Avoid imports from CRK-1, AAES-OS, or any candidate implementation.
3. Run identical positive, negative, replay, migration, and interoperability fixtures against every candidate.
4. Verify canonical events, object hashes, approvals, CCRs, admission lineage, and terminal audit.
5. Publish machine-readable results with suite/version, candidate/version, environment, tests, failures, evidence, timestamps, and verifier.
6. Distinguish specification ambiguity, suite defect, implementation defect, and environmental failure.
7. Require an independent verifier for certification claims.
8. Revoke or expire certification when the implementation, contract, or required evidence changes.

CCS may certify CRK-1, but CRK-1 cannot certify itself and cannot define CCS expected results through its own behavior.
