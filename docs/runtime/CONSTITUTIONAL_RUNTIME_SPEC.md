# Constitutional AI Runtime Specification v1.0

Status: ARCHITECTURALLY FROZEN  
Authority: Internal platform contract  
Execution loop: `Intent -> Planning -> Governance -> Execution -> Evidence -> Reflection -> State -> Learning`

Deployment companion: [Constitutional AI Runtime Deployment Blueprint](./DEPLOYMENT_BLUEPRINT.md)

Integrated lifecycle companion: [CEIP v1.0 Reference Runtime](./CEIP_V1_REFERENCE_RUNTIME.md)

## Constitutional center

Models, tools, agents, and orchestration provide capability; they possess no authority by default. Authority exists only in the constitutional execution loop. Capability loss must not cause identity loss, and capability gain must not imply authority gain.

The frozen core consists of Intent, ISL Planning, CIEMS Governance, Orchestration, Substrate Registry, Substrate Adapters, Evidence, Reflection, State, Learning, Knowledge Graph, and Identity. A new core module requires a documented engineering necessity and constitutional review.

## 1. CIEMS constitutional kernel

CIEMS is a fail-closed, deterministic constitutional membrane around every meaningful boundary crossing.

### Services

- `IntentKernel.ValidateIntent(Intent) -> IntentStatus`: validates schema, actor, context snapshot, ISL program, and authorization.
- `PlanKernel.ValidatePlan(SubstratePlan) -> PlanStatus`: validates sovereignty scope, risk, evidence preconditions, CIC/CCC constraints, capabilities, and registered substrates.
- `ExecutionKernel.AuthorizeExecution(planId) -> ExecutionToken`: validates plan approval, actor validity, context freshness, and resource limits.
- `EvidenceKernel.AcceptEvidence(EvidenceRecord) -> EvidenceStatus`: validates intent/plan/step/substrate provenance, type, integrity, and admissibility.
- `USSKernel.ApplyUSSUpdate(USSUpdate) -> UpdateStatus`: validates graph target, continuity, inference traceability, evidence linkage, and conflict disposition.

### Invariants

- K1: No execution without a valid Intent.
- K2: No substrate invocation without an approved, immutable SubstratePlan.
- K3: No USS state mutation without an accepted EvidenceRecord.
- K4: Evidence, execution, and updates must be fully provenance-linked.
- K5: The orchestrator may execute only what an unexpired ExecutionToken authorizes.

### ExecutionToken minimum binding

`planId`, `planHash`, `actorId`, `contextSnapshotId`, authorized capabilities, authorized substrates, expiration, risk profile, execution budget, issuer, and integrity proof.

## 2. ISL planning engine

ISL is the formal planning brain; CIEMS is the governance brain.

`CompileIntent(Intent, ContextSnapshot) -> SubstratePlan`

1. Parse: match `Intent.type` to an `IntentSpec` in a versioned `ISLProgram`.
2. Analyze: query USS for evidence, identity, mission, and preconditions.
3. Select: query validated registry capability assertions within the policy envelope.
4. Plan: emit ordered `SubstrateStep[]`, `GovernanceProfile`, evidence requirements, fallback paths, and `PlanProvenance`.
5. Emit: submit the immutable plan to `PlanKernel`; ISL cannot authorize it.

## 3. Unified Sovereign Substrate (USS)

USS is the authoritative constitutional state, not a chat history or undifferentiated memory store.

Partitions: Identity, Evidence, Reputation, Mission, Temporal, Lineage, and Multiverse. Every node and edge records `assertionClass`, `epistemicStatus`, `authority`, `confidence`, validity interval, provenance, evidence ID, update ID, and supersession state.

Services:

- `GraphWriteService.ApplyUSSUpdate(update) -> UpdateStatus`
- `GraphQueryService.QueryGraph(graphId, query) -> ResultSet`
- `GraphReplayService.ReplayState(graphId, timestampOrVersion) -> GraphSnapshot`

Updates are atomic and versioned. Constitutional state transitions are strongly consistent.

### Evidence disposition

Every accepted EvidenceRecord must produce a governed disposition, but need not mutate substantive state: `APPLIED`, `CORROBORATES_EXISTING_STATE`, `CONTRADICTS_EXISTING_STATE`, `DEFERRED`, `REJECTED_FOR_UPDATE`, `REQUIRES_REVIEW`, or `NO_STATE_CHANGE`. No evidence disappears silently.

## 4. Substrate adapter contract

All substrate access occurs through an adapter implementing a versioned `SubstrateIntegrationContract` containing provider, SPDX license, schemas, invocation mode, evidence/sovereignty policies, risk, audit hooks, endpoint, authentication, health checks, timeouts, retention and egress constraints.

`AdapterInstance.Invoke(InternalInput, ExecutionContext) -> SubstrateInvocationResult`

The adapter validates the ExecutionToken, transforms input, invokes the provider, validates output, emits audit events, and constructs provenance-bound candidate evidence. It normalizes capability without inheriting authority.

## 5. Open-source substrate registry

APIs: `RegisterSubstrate`, `GetSubstrate`, `ListSubstrates`, and `DeprecateSubstrate`.

Discovery filters include capability, provider, license, risk profile, governance profile, and lifecycle status. Capability is represented by a `CapabilityAssertion` with asserted-by, evidence references, validation status, valid context, test date, expiry, operating constraints, and known failure modes. ISL plans against validated assertions, not marketing labels.

## 6. Deployable topology

`Substrates -> Adapters -> Registry -> CIEMS IntentGate -> ISL -> CIEMS PlanGate/ExecutionGate -> Orchestration -> Adapters/Substrates -> CIEMS EvidenceGate/USSUpdateGate -> USS -> Interfaces`

CIEMS surrounds the path; it is not merely a downstream box. PARAGON One and other products consume stable high-level services—Missions, Recommendations, Mentor, Learning, Research, Organizations, Projects, Portfolio, Reputation, Authentication, and Messaging—and never access plans, adapters, or internal graphs directly.

## Readiness gate

The platform may be called production-ready only when stable APIs, SDK, test suite, conformance suite, developer documentation, and reference implementation have reproducible build, lint, test, replay, security, performance, deployment, and release evidence. External deployment and independent review must be labeled pending until actually performed.

## Deployment architecture

- Secure core VPC: CIEMS, ISL, orchestration, and the USS data plane.
- Data plane: clustered graph storage with versioned updates/replay plus an append-only telemetry and audit store.
- Governed substrate VPCs: stateless Adapter Runtime services and isolated local/remote substrate services.
- Access plane: API Gateway exposing Intent, query, product, and restricted administration APIs.
- Interfaces: AI Twin, consoles, worlds, and product UIs communicate only through the gateway.

Cross-zone traffic uses authenticated service identities, explicit allowlists, encryption, request IDs, and policy enforcement. The runtime has no implicit east-west trust.

## Runtime services

- `IntentService.SubmitIntent(Intent) -> IntentId` invokes IntentKernel and starts ISL compilation.
- `PlanningService.GeneratePlan(IntentId) -> PlanId` wraps ISL and PlanKernel.
- `ExecutionService.ExecutePlan(PlanId) -> EvidenceRecord[]` obtains an ExecutionToken and coordinates adapters.
- `EvidenceService.RecordEvidence(EvidenceRecord) -> EvidenceId` admits or disposes evidence through EvidenceKernel.
- `USSService.ApplyUpdate`, `Query`, and `Replay` mediate every graph operation.
- `RegistryService.RegisterSubstrate`, `ListSubstrates`, `GetSubstrate`, and `DeprecateSubstrate` own the capability catalog.

## Security model

Humans, AI Twins, workloads, and system agents have distinct identities. OAuth/OIDC and short-lived JWTs terminate at the gateway; service-to-service communication uses mTLS workload identities. Authorization is actor-, mission-, graph-, capability-, and substrate-scoped. USS partitions enforce identity and sovereignty boundaries. Secrets remain in a managed secret store and never enter plans or evidence. Every artifact and transition is integrity-bound, timestamped, and auditable. Adapter egress is deny-by-default. Least-privilege roles, resource budgets, expiration, revocation, replay protection, and fail-closed policy evaluation are mandatory.

## Governance contracts

- Constitutional Execution Contract: formal Intent -> Plan -> Token -> Evidence -> Disposition/USSUpdate invariants.
- Sovereignty Contract: actor, mission, data, jurisdiction, retention, and substrate scopes.
- Risk and Compliance Contract: substrate risk, allowed contexts, controls, regulatory mappings, and escalation paths.
- CIC: every inference is traceable to admissible evidence and the producing execution.
- CCC: state transitions preserve identity, authority, lineage, temporal continuity, and supersession semantics.

Contracts are versioned, hash-bound, referenced by ISL programs and registry entries, and enforced by CIEMS—not advisory documentation.

## Substrate onboarding pipeline

1. Discover the open-source substrate and collect authoritative interface, license, provenance, and failure-mode documentation.
2. Author the SubstrateIntegrationContract and capability assertions.
3. Perform license, security, sovereignty, privacy, compliance, and risk review.
4. Implement the adapter and input/output/evidence transformations.
5. Run unit, integration, negative, timeout, malformed-output, egress, and conformance tests.
6. Register only validated capabilities and issue a versioned registry receipt.
7. Amend relevant ISL programs without widening unrelated intent authority.
8. Monitor health, drift, cost, incidents, validation expiry, and deprecation.

Registration is not self-certification; failed or expired validation leaves the substrate unavailable to planning.

## AI Twin integration

An AI Twin is a first-class but non-sovereign actor with its own IdentityId, mission, reputation, evidence, and lineage. It submits intents through IntentService, and its plans/executions follow the identical CIEMS path used for humans. It reads authorized product projections from USS through USSService and records reflections as provenance-bound candidate evidence. Delegated actions bind both user and Twin identities. The Twin cannot exceed the user's delegated authority, call adapters or substrates directly, mutate USS directly, approve its own plan, conceal its reasoning, or convert capability into authority.
