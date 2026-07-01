# Architect Agent Security Boundary

## Scope

`@aaes-os/architect-agent` is a deterministic, in-memory governance
orchestrator. Its public runtime surface derives contracts, produces mutation
proposals, constructs reversible envelopes, replays integration, applies the
safety veto, and creates an evidence receipt object.

The package does not apply mutations. An `ALLOW` verdict authorizes the
returned envelope under the supplied contract; it does not modify a workspace.

## Runtime Side Effects

The runtime package performs:

- CPU-only SHA-256 and SHA3-256 hashing;
- in-memory object construction, validation, freezing, and comparison.

The runtime package performs no:

- filesystem reads or writes;
- network requests;
- child process execution;
- environment-variable reads or writes;
- dynamic `eval`, `Function` construction, or dynamic code loading;
- system clock reads through `ArchitectAgentLoop`;
- mutation application or receipt persistence.

`ArchitectAgentLoop.execute()` requires the caller to provide `issued_at` and
passes it to the evidence-receipt builder. This keeps repeated acts independent
of the ambient clock.

The `scripts/smoke-dist.mjs` release test is development and CI tooling outside
this runtime boundary. It builds packages, launches pnpm and Node, and writes
only inside a unique operating-system temporary directory that it removes.

## Trusted And Untrusted Inputs

Treat all caller-supplied situations, target paths, pre-state content, contract
objects, and timestamps as untrusted.

The package enforces:

- nonempty, unique targets and risk-based file-count caps;
- UGR-to-CMC contract lineage through the orchestrated path;
- runtime authorization by the CMC;
- complete and ordered target-set closure;
- aggregate pre-state hash agreement;
- exact restore or delete inverse patches;
- patch and envelope hash integrity;
- internal EGL-1 comparison of original and replayed integrations;
- fail-closed handling for missing replay data and empty envelope sets.

The caller remains responsible for:

- authenticating users and authorizing the requested targets;
- proving that supplied pre-state content matches the real workspace;
- constraining path syntax and workspace containment before mutation;
- limiting input byte size and execution resource use;
- persisting and protecting receipts;
- applying envelopes atomically;
- sandboxing mutation executors;
- durable append-only ledgers, trust anchors, and key-backed signing.

## Sensitive Data

Exact reversibility requires a `restore` reverse patch to contain the prior file
content. Governed act objects and serialized envelopes can therefore contain
source code, credentials, personal data, or other sensitive material from the
pre-state snapshot.

Do not place raw acts or envelopes in public logs. Evidence receipts contain
deterministic identifiers and a subject hash, not the reverse-patch content.

## Integrity Is Not Authority

SHA-256 envelope identifiers and SHA3-256 evidence-receipt identifiers detect
drift and bind deterministic data. They do not establish:

- user or service identity;
- authentication or authorization;
- possession of a private key;
- timestamp authority;
- non-repudiation;
- durable ledger inclusion.

Production authority requires a separate key-backed signer and durable,
append-only evidence store.

## Threat Summary

| STRIDE | Package Threat | Mitigation Or Boundary |
|---|---|---|
| Spoofing | A caller submits a forged EGL equivalence claim. | `SafetyRuntime` compares original and replayed integrations itself; it accepts no external equivalence flag. Caller identity remains out of scope. |
| Tampering | Patch content or envelope metadata changes after construction. | Safety recomputes patch and envelope hashes and returns `DENY` on mismatch. Mutation executors must revalidate immediately before applying. |
| Repudiation | A caller denies proposing or applying an act. | Deterministic receipts bind act metadata, but no signature or durable ledger is provided, so cryptographic non-repudiation is out of scope. |
| Information disclosure | Reverse patches expose prior file content. | Acts and envelopes must be handled as sensitive. Receipts retain hashes rather than raw reverse content. |
| Denial of service | A situation requests excessive files or very large content. | The bridge caps file counts by risk and rejects duplicates. Byte-size, CPU, and memory quotas remain the caller's responsibility. |
| Elevation of privilege | A forged build omits, reorders, or adds targets. | Integration and safety require the exact ordered CMC target set. Authorization of that CMC and filesystem containment remain caller responsibilities. |

## Reporting

Report suspected vulnerabilities privately to the AAES-OS maintainers. Include
the affected package version, a minimal reproduction, the violated invariant,
and whether raw pre-state content or receipt identifiers were exposed.
