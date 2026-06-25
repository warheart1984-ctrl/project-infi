# AAES-OS — Language-Agnostic Interface Spec v1

| Field | Value |
|-------|-------|
| **Spec** | `aaes_os.interface.v1` |
| **Trace spec** | [AAES_OS_V1_FORMAL_SPEC.md](./AAES_OS_V1_FORMAL_SPEC.md) (`aaes_os.v1.0`) |
| **Architecture** | [AAES_OS_ARCHITECTURE_V1.md](./AAES_OS_ARCHITECTURE_V1.md) |
| **Starter repo** | [archive/cold-storage/reference/aaes-os-starter/](../../archive/cold-storage/reference/aaes-os-starter/) (live product: [aaes-os/](../../aaes-os/)) |
| **Module id** | `AAIS-AAES-OS-01` |
| **Status** | Normative contract (Standards Track) |

Mythic label (docs only): **AAES-OS**. Engineering package: `aaes_os` (`src/aaes_os/`).

Normative sections 1–4 define the cognitive pipeline surface. Section 7 reconciles this layer with the governed-span RFC and Python reference.

---

## 1. Core Data Types

### TypeScript

```ts
export interface AAESRequest {
  id: string
  actorId: string
  timestamp: string
  channel: string
  payload: any
  scope: Scope
  constraints?: Constraint[]
}

export interface AAESContext {
  request: AAESRequest
  traceId: string
  session: Record<string, any>
  policies: PolicySet
}

export interface AAESStep {
  stepId: string
  stage: "perception" | "deliberation" | "planning" | "action" | "check"
  input: any
  output: any
  metadata?: Record<string, any>
}

export interface AAESDecision {
  decisionId: string
  rationale: string
  selectedPlan: AAESPlan
  rejectedPlans: AAESPlan[]
}

export interface AAESAction {
  actionId: string
  target: string
  parameters: any
  preconditions?: any
  postconditions?: any
}
```

### Rust

```rust
pub struct AAESRequest {
    pub id: String,
    pub actor_id: String,
    pub timestamp: String,
    pub channel: String,
    pub payload: serde_json::Value,
    pub scope: Scope,
    pub constraints: Option<Vec<Constraint>>,
}

pub struct AAESContext {
    pub request: AAESRequest,
    pub trace_id: String,
    pub session: serde_json::Value,
    pub policies: PolicySet,
}

pub struct AAESStep {
    pub step_id: String,
    pub stage: Stage,
    pub input: serde_json::Value,
    pub output: serde_json::Value,
    pub metadata: Option<serde_json::Value>,
}

pub struct AAESDecision {
    pub decision_id: String,
    pub rationale: String,
    pub selected_plan: AAESPlan,
    pub rejected_plans: Vec<AAESPlan>,
}

pub struct AAESAction {
    pub action_id: String,
    pub target: String,
    pub parameters: serde_json::Value,
    pub preconditions: Option<serde_json::Value>,
    pub postconditions: Option<serde_json::Value>,
}
```

Supporting types (`Scope`, `Constraint`, `PolicySet`, `Stage`, `AAESPlan`, `ActionResult`, `InvariantResult`, `PolicyResult`) are defined in the starter [`archive/cold-storage/reference/aaes-os-starter/src/core/types.ts`](../../archive/cold-storage/reference/aaes-os-starter/src/core/types.ts).

---

## 2. Cognitive Pipeline Interfaces

### TypeScript

```ts
export interface PerceptionEngine {
  perceive(req: AAESRequest): Promise<AAESContext>
}

export interface DeliberationEngine {
  deliberate(ctx: AAESContext): Promise<AAESPlan[]>
}

export interface PlanningEngine {
  selectPlan(ctx: AAESContext, plans: AAESPlan[]): Promise<AAESDecision>
}

export interface ActionEngine {
  execute(ctx: AAESContext, decision: AAESDecision): Promise<ActionResult[]>
}
```

### Rust

```rust
pub trait PerceptionEngine {
    fn perceive(&self, req: AAESRequest) -> anyhow::Result<AAESContext>;
}

pub trait DeliberationEngine {
    fn deliberate(&self, ctx: &AAESContext) -> anyhow::Result<Vec<AAESPlan>>;
}

pub trait PlanningEngine {
    fn select_plan(&self, ctx: &AAESContext, plans: Vec<AAESPlan>) -> anyhow::Result<AAESDecision>;
}

pub trait ActionEngine {
    fn execute(&self, ctx: &AAESContext, decision: AAESDecision) -> anyhow::Result<Vec<ActionResult>>;
}
```

---

## 3. Governance Layer

### TypeScript

```ts
export interface InvariantEngine {
  check(stage: string, ctx: AAESContext, step: AAESStep): Promise<InvariantResult>
}

export interface PolicyEngine {
  evaluate(target: "plan" | "action", ctx: AAESContext, item: any): Promise<PolicyResult>
}
```

### Rust

```rust
pub trait InvariantEngine {
    fn check(&self, stage: Stage, ctx: &AAESContext, step: &AAESStep) -> anyhow::Result<InvariantResult>;
}

pub trait PolicyEngine {
    fn evaluate(&self, target: TargetType, ctx: &AAESContext, item: &serde_json::Value) -> anyhow::Result<PolicyResult>;
}
```

---

## 4. Module Registry (Daniel, others)

### TypeScript

```ts
export interface ExecutionModule {
  name: string
  canHandle(action: AAESAction): boolean
  execute(action: AAESAction, ctx: AAESContext): Promise<ActionResult>
}
```

### Rust

```rust
pub trait ExecutionModule {
    fn name(&self) -> &'static str;
    fn can_handle(&self, action: &AAESAction) -> bool;
    fn execute(&self, action: &AAESAction, ctx: &AAESContext) -> anyhow::Result<ActionResult>;
}
```

---

## 5. Starter repo layout (informative)

Canonical TypeScript scaffold: [`archive/cold-storage/reference/aaes-os-starter/`](../../archive/cold-storage/reference/aaes-os-starter/).

```
aaes-os/
├── README.md
├── LICENSE
├── docs/
│   ├── architecture.md
│   ├── invariants.md
│   └── cognitive_pipeline.md
├── src/
│   ├── core/
│   ├── pipeline/
│   ├── governance/
│   ├── modules/daniel/
│   ├── uls/
│   └── orchestrator.ts
├── tests/
└── manifests/modules.toml
```

Trace-layer stubs (RFC `TraceEvent` / `TraceBus`): [`archive/cold-storage/reference/aaes_os_v1/`](../../archive/cold-storage/reference/aaes_os_v1/).

---

## 6. Stub orchestrator

Minimal contract (invariants only):

### TypeScript

```ts
export class AAESOrchestrator {
  constructor(
    private perception: PerceptionEngine,
    private deliberation: DeliberationEngine,
    private planning: PlanningEngine,
    private action: ActionEngine,
    private invariants: InvariantEngine
  ) {}

  async handle(req: AAESRequest) {
    const ctx = await this.perception.perceive(req)
    const plans = await this.deliberation.deliberate(ctx)
    const decision = await this.planning.selectPlan(ctx, plans)
    return await this.action.execute(ctx, decision)
  }
}
```

### Rust

```rust
pub struct AAESOrchestrator<P, D, PL, A, I>
where
    P: PerceptionEngine,
    D: DeliberationEngine,
    PL: PlanningEngine,
    A: ActionEngine,
    I: InvariantEngine,
{
    pub perception: P,
    pub deliberation: D,
    pub planning: PL,
    pub action: A,
    pub invariants: I,
}

impl<P, D, PL, A, I> AAESOrchestrator<P, D, PL, A, I>
where
    P: PerceptionEngine,
    D: DeliberationEngine,
    PL: PlanningEngine,
    A: ActionEngine,
    I: InvariantEngine,
{
    pub fn handle(&self, req: AAESRequest) -> anyhow::Result<Vec<ActionResult>> {
        let ctx = self.perception.perceive(req)?;
        let plans = self.deliberation.deliberate(&ctx)?;
        let decision = self.planning.select_plan(&ctx, plans)?;
        self.action.execute(&ctx, decision)
    }
}
```

The **reference starter** implements the full step-traced orchestrator (per-stage `AAESStep`, `InvariantEngine.check`, `AuditLogger`) in [`archive/cold-storage/reference/aaes-os-starter/src/orchestrator.ts`](../../archive/cold-storage/reference/aaes-os-starter/src/orchestrator.ts). An extended product copy may also exist at [`aaes-os/`](../../aaes-os/) in the monorepo.

---

## 7. Reconciliation — cognitive pipeline ↔ RFC trace ↔ Python

### 7.1 Two admission layers

| Layer | Purpose | Canonical types |
|-------|---------|-----------------|
| **Cognitive pipeline** (§1–4) | Operator request → plans → actions | `AAESRequest` with `id`, `actorId`, `scope`, … |
| **Governed span RFC** | Append-only trace bus | `TraceEvent`, `GovernedSpan`, `RuntimeContext` |

A complete product bridges pipeline steps to trace events:

| Pipeline `stage` | Typical `TraceEvent.event_type` | `SpanState` after |
|------------------|--------------------------------|-------------------|
| `perception` / `deliberation` | `INTENT` | `INTENTED` |
| `planning` | `DECISION` | `DECIDED` |
| `action` | `EXECUTION` then `RESULT` | `EXECUTING` → `RESULTED` → `CLOSED` |

Formal rules: [AAES_OS_V1_FORMAL_SPEC.md](./AAES_OS_V1_FORMAL_SPEC.md) §2–§7.

### 7.2 Field naming conventions

| Surface | Convention | Example |
|---------|------------|---------|
| TypeScript / JSON HTTP | `camelCase` | `actorId`, `traceId`, `stepId` |
| Rust / Python dataclasses | `snake_case` | `actor_id`, `trace_id`, `step_id` |

Serializers MUST translate at the API boundary. Python `AuthEnvelope.actor_id` maps to JSON `actor_id` (RFC) or `actorId` (cognitive HTTP) per endpoint contract.

### 7.3 Python `src/aaes_os/` mapping

| Interface §1 type | Python module | Notes |
|-------------------|---------------|-------|
| `AAESRequest` (§1) | `pipeline_types.AAESRequest` | `prompt`, `actor_id`, `session_id` — cognitive shape; map `id`↔`trace_id`, `payload`↔`prompt` at bridge |
| `AAESRequest` (trace admission) | `api_types.AAESRequest` | `trace_id`, `intent_payload`, `runtime_context`, `auth` — RFC-aligned |
| `AAESContext` | `pipeline_types.AAESContext` / `api_types.AAESContext` | Pipeline vs span+bus contexts |
| `AAESStep` | `pipeline_types.AAESStep` | `step_type` enum vs string `stage` |
| `AAESDecision` | `pipeline_types.AAESDecision` | `verdict` vs `selectedPlan` |
| `AAESAction` | `pipeline_types.AAESAction` | `module_id`/`operation` vs `target`/`parameters` |
| `TraceEvent` | `models.TraceEvent` | Normative RFC record |
| `GovernedSpan` | `governed_span.GovernedSpan` | Span state machine |
| `TraceBus` | `trace_bus.TraceBusValidator` | `validate_and_append` |
| `InvariantEngine` | `invariant_engine.InvariantEngine` | Span + pipeline checks |
| `PolicyEngine` | `policy_engine.PolicyEngine` | Admission policy |
| `ExecutionModule` / Daniel | `modules/daniel.py` | Pluggable executor |
| `governedAction` | `action.governed_action` | Four-event happy path helper |

### 7.4 Seven Invariants ↔ RFC INV-1..7

| Seven Invariants (architecture) | RFC id | Enforced by |
|-----------------------------------|--------|-------------|
| Traceability | INV-2 | `TraceBusValidator`, `DefaultInvariantEngine` |
| Integrity of State | INV-5 | Span state machine |
| Identity & Auth | INV-1 | `AuthEnvelope` |
| Scope & Boundaries | *(pipeline)* | `scope` on `AAESRequest`, policy engine |
| Explainability Hook | INV-4 | `RuntimeContext`, ULS `summarize_trace` |
| Reversibility / Failsafe | INV-6 | `rollback_possible` on `RESULT` |
| Governance First | INV-7 | No `EXECUTION` without `DECISION` |

---

## 8. Related paths

| Path | Role |
|------|------|
| [archive/cold-storage/reference/aaes-os-starter/](../../archive/cold-storage/reference/aaes-os-starter/) | **Coding agent start here** — cognitive pipeline TS scaffold |
| [archive/cold-storage/reference/aaes_os_v1/](../../archive/cold-storage/reference/aaes_os_v1/) | Trace bus TS/Rust stubs |
| [src/aaes_os/](../../src/aaes_os/) | Python reference implementation |
| [tests/test_aaes_os_v1.py](../../tests/test_aaes_os_v1.py) | RFC trace layer tests |

---

## 9. Version

- Interface: `aaes_os.interface.v1`
- Trace formal spec: `aaes_os.v1.0`
- Invariant set: `aaes_os_invariants.v1`
