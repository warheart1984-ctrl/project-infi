# Constitutional AI Runtime Deployment Blueprint v1.0

Manifest-generation companion: [Kubernetes and Service Mesh Generation Blueprint](./KUBERNETES_GENERATION_BLUEPRINT.md).

Status: Frozen deployment architecture  
Companion specification: [Constitutional Runtime Specification](./CONSTITUTIONAL_RUNTIME_SPEC.md)

## 1. Deployment domains

### Control plane

- `governance.*`: CIEMS Intent, Plan, Execution, Evidence, and USS kernels.
- `planning.*`: ISL compiler and versioned program registry.
- `orchestration.*`: approved-plan executor and execution-state coordinator.

The control plane runs in the secure core network. It coordinates work but does not store authoritative graph state or invoke raw substrates directly.

### Data plane

- `storage.uss.*`: partitioned graph storage, versioned state transitions, snapshots, and replay.
- `storage.audit.*`: append-only logs, traces, metrics, decisions, receipts, and integrity proofs.

Only USS storage services may commit graph mutations. Audit records are append-only and retained independently from operational graph projections.

### Substrate plane

- `substrate.adapter.*`: stateless adapter instances that validate execution context and normalize input/output.
- `substrate.raw.*`: isolated local or remote models, tools, agents, and frameworks.

Raw substrates have no route to the control plane, USS, or access plane. Adapter egress is allowlisted per registered contract.

### Access plane

- `interface.gateway`: public Intent, product, query, and restricted administration APIs.
- `interface.product.*`: AI Twin, Console, World, and product backends.

Interfaces communicate through the gateway only. They cannot address CIEMS internals, ISL artifacts, adapters, raw substrates, or storage nodes directly.

### Canonical flow

```text
Interface
  -> API Gateway
  -> CIEMS IntentKernel
  -> ISL Planning Engine
  -> CIEMS PlanKernel + ExecutionKernel
  -> Orchestration Engine
  -> Adapter Runtime
  -> Raw Substrate
  -> CIEMS EvidenceKernel
  -> CIEMS USSKernel
  -> USS Graph Storage
  -> authorized projection through Gateway
  -> Interface
```

## 2. Service mesh topology

Each service workload has a mesh proxy responsible for workload identity, mTLS, authorization policy, telemetry, bounded retries, timeouts, and circuit breaking. Application code must not implement a shadow routing path around the proxy.

### Required authorization matrix

| Caller | Permitted destination | Purpose |
|---|---|---|
| `interface.*` | `interface.gateway` | Product/API access |
| `interface.gateway` | `governance.intent`, approved query services | Submit intent and read projections |
| `governance.intent` | `planning.compiler` | Request planning after intent approval |
| `planning.*` | `registry.*`, read-only `storage.uss.query`, `governance.plan` | Discover validated capabilities and emit plans |
| `governance.execution` | `orchestration.executor` | Deliver hash-bound execution token |
| `orchestration.*` | `substrate.adapter.*` | Execute authorized plan steps |
| `substrate.adapter.*` | contract-allowlisted `substrate.raw.*` | Invoke registered substrate |
| `orchestration.*` | `governance.evidence` | Submit candidate evidence |
| `governance.uss` | `storage.uss.write` | Commit approved state transition |
| authorized services | `storage.audit.*` | Append trace/audit events |

Everything not explicitly allowed is denied. In particular:

- Only `orchestration.*` may invoke `substrate.adapter.*`.
- Only `governance.*` may approve or deny intent, planning, execution, evidence, and updates.
- Only `storage.uss.write` may mutate graph state, and it accepts writes only from `governance.uss`.
- No workload may call `substrate.raw.*` except its authorized adapter.
- Retry policy never retries a non-idempotent execution or graph mutation without an idempotency key.

## 3. Constitutional kernel boot sequence

The kernel moves through explicit states: `COLD`, `CONTRACTS_LOADED`, `IDENTITIES_READY`, `PROFILES_READY`, `WIRED`, `GOVERNED`, or `FAILED_CLOSED`.

1. Load and hash the Constitution, Constitutional Execution Contract, Sovereignty Contract, Risk and Compliance Contract, CIC, and CCC.
2. Validate signatures, schema versions, precedence, compatibility, and required invariants. Any failure enters `FAILED_CLOSED`.
3. Initialize system identities, workload identities, administrator roles, service accounts, and revocation lists.
4. Register governance profiles and bind supported intents, missions, data scopes, risk bands, and substrate classes.
5. Initialize IntentKernel, PlanKernel, ExecutionKernel, EvidenceKernel, and USSKernel with the same immutable contract set.
6. Establish authenticated connections to USS query/write/replay services, the registry, and the audit store.
7. Verify that bypass routes are absent by running negative connectivity and unauthorized-write probes.
8. Emit a signed boot receipt containing contract hashes, service identities, profile versions, dependency health, and probe results.
9. Enter `GOVERNED` only if every required check passes.

Before `GOVERNED`, the gateway rejects new intents and orchestration rejects tokens. After `GOVERNED`, an ungoverned execution or state-write path is a critical incident that forces fail-closed isolation.

## 4. AI Twin lifecycle

### Birth

Create a unique Twin IdentityId and initial Identity, Mission, Reputation, and Lineage nodes through a governed provisioning intent. Record creator, constitution version, model/strategy baseline, and birth receipt.

### Bonding

Create explicit delegation edges between human and Twin identities. Issue a versioned Sovereignty Contract defining readable graph scopes, permitted intent types, mission bounds, action budgets, time limits, approval requirements, and revocation conditions.

### Operation

The Twin submits intents through IntentService. It cannot approve its own intent or plan. All executions use hash-bound tokens, and all observations/actions create provenance-linked evidence or a governed rejection. USS reads return authorized projections rather than raw unrestricted graphs.

### Evolution

Reflection and learning may propose evidence-backed changes to reputation, mission, lineage, preferences, or strategies. Each change requires an evidence disposition and, where state changes, a CCC/CIC-compliant USSUpdate. Model replacement does not replace Twin identity.

### Suspension and retirement

Suspension temporarily blocks new intents and tokens while preserving state. Retirement marks the Twin inactive, revokes delegations and credentials, invalidates outstanding tokens, prevents new intents, and preserves its complete USS and audit lineage. Reactivation requires a new governed authorization rather than reversing history.

## 5. USS partitioning strategy

### Partition keys

- Sovereignty: `tenantId / identityScopeId` for user and organization isolation.
- Graph class: Identity, Evidence, Reputation, Mission, Temporal, Lineage, or Multiverse.
- Time bucket: event-time partitions for high-volume Evidence, Activity, audit, and temporal edges.
- Optional jurisdiction: data-residency boundary when required by the Sovereignty Contract.

An authoritative record carries stable global IDs even when projections are partitioned. Cross-partition edges are references resolved by governed query services, not unrestricted database joins.

### Storage behavior

- Identity and authority writes use strong consistency and conservative replication.
- Evidence is append-oriented; corrections supersede rather than overwrite.
- Reputation and mission projections are reproducible from evidence and versioned rules.
- Temporal partitions preserve event time and ingestion time.
- Lineage preserves branch/merge ancestry.
- Multiverse objects are explicitly hypothetical and never silently promoted to factual graphs.
- Replay uses immutable update logs plus periodic signed snapshots.

Encryption keys, retention, export, deletion, backup, and replica placement follow the owning Sovereignty Contract. A cross-identity query requires explicit delegated scope and produces an audit record.

## 6. Automated substrate onboarding pipeline

The pipeline state machine is:

```text
DISCOVERED -> CONTRACT_DRAFT -> UNDER_REVIEW -> ADAPTER_TESTING
-> CANDIDATE -> VALIDATED -> ACTIVE -> DEPRECATED -> RETIRED
```

Any failed gate moves the candidate to `REJECTED` or `QUARANTINED`; promotion is never automatic solely because code compiles.

1. **Intake**: submit repository, immutable revision/digest, maintainers, documentation, interface, SPDX license, provenance, deployment mode, and known failure modes.
2. **Contract generation**: scaffold schemas, capabilities, invocation mode, health/timeouts, evidence rules, sovereignty/egress/retention policies, risk profile, model digest, and audit hooks.
3. **Governance analysis**: perform license, supply-chain, vulnerability, privacy, jurisdiction, data-egress, compliance, and authority-impact classification.
4. **Adapter scaffolding**: generate contract-bound adapter structure; developers implement only provider-specific translation and invocation.
5. **Automated validation**: run schema, unit, integration, malformed-input/output, timeout, cancellation, retry/idempotency, provenance, policy-denial, sandbox, egress, and evidence conformance tests.
6. **Candidate registration**: issue a substrate ID with `candidate` status. Candidate substrates are unavailable to production ISL programs.
7. **Sandbox promotion**: execute representative and adversarial ISL plans in an isolated environment; attach results and reviewer approval to capability assertions.
8. **Activation**: mark validated capability assertions active, set expiry/revalidation dates, and update only explicitly approved ISL IntentSpecs.
9. **Lifecycle monitoring**: track availability, drift, incidents, cost, performance, validation expiry, upstream changes, license changes, and policy violations.
10. **Deprecation/retirement**: block new planning, allow governed completion or cancellation of existing work, revoke credentials, preserve evidence, and provide migration guidance.

## Deployment acceptance gates

- Contract and boot receipts validate.
- Mesh deny-by-default probes pass.
- No direct substrate or USS mutation path exists.
- Backup, restore, replay, and disaster-recovery exercises pass.
- Security and load tests meet declared thresholds.
- Observability correlates IntentId, PlanId, ExecutionTokenId, stepId, substrateId, EvidenceId, and USSUpdateId.
- Rollback and key/token revocation are rehearsed.
- Production promotion has a signed release and independent verification receipt.
