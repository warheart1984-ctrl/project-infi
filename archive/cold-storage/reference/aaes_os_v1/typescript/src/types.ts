/** AAES-OS v1 interface types — see docs/contracts/AAES_OS_INTERFACE_V1.md */

export enum EventType {
  INTENT = "INTENT",
  DECISION = "DECISION",
  EXECUTION = "EXECUTION",
  RESULT = "RESULT",
}

export enum SpanState {
  INIT = "INIT",
  INTENTED = "INTENTED",
  DECIDED = "DECIDED",
  EXECUTING = "EXECUTING",
  RESULTED = "RESULTED",
  CLOSED = "CLOSED",
}

export enum Role {
  USER = "USER",
  RUNTIME = "RUNTIME",
  EXECUTOR = "EXECUTOR",
  GOVERNOR = "GOVERNOR",
  OBSERVER = "OBSERVER",
}

export enum StepType {
  INGRESS = "INGRESS",
  INVARIANT_CHECK = "INVARIANT_CHECK",
  POLICY_EVAL = "POLICY_EVAL",
  MODULE_ROUTE = "MODULE_ROUTE",
  DECIDE = "DECIDE",
  EXECUTE = "EXECUTE",
  VERIFY = "VERIFY",
  EMIT_TRACE = "EMIT_TRACE",
  COMPLETE = "COMPLETE",
}

export enum InvariantId {
  SI_AUTHENTICITY = "SI_AUTHENTICITY",
  SI_TRACEABILITY = "SI_TRACEABILITY",
  SI_CAUSALITY = "SI_CAUSALITY",
  SI_RECONSTRUCTABILITY = "SI_RECONSTRUCTABILITY",
  SI_IDENTITY = "SI_IDENTITY",
  SI_REVERSIBILITY = "SI_REVERSIBILITY",
  SI_CONSTITUTION = "SI_CONSTITUTION",
}

export interface AuthEnvelope {
  role: Role;
  actor_id: string;
  signature_hash: string;
}

export interface RuntimeContext {
  runtime_version: string;
  invariant_version: string;
  prompt_hash: string;
  decision_policy_hash: string;
  toolchain_hash: string;
  memory_snapshot_hash: string;
}

export interface TraceEvent {
  event_id: string;
  span_id: string;
  event_type: EventType;
  timestamp_utc: string;
  auth: AuthEnvelope;
  runtime_context: RuntimeContext;
  payload: Record<string, unknown>;
  parent_event_id: string | null;
  parent_span_id: string | null;
  event_hash: string;
}

export interface ReconstructedSpan {
  span_id: string;
  state: SpanState;
  events: TraceEvent[];
  runtime_context: RuntimeContext;
}

export interface GovernedSpan {
  readonly span_id: string;
  readonly parent_span_id: string | null;
  state: SpanState;
  runtime_context: RuntimeContext | null;
  close(): void;
}

export interface AAESRequest {
  trace_id: string;
  intent_payload: Record<string, unknown>;
  runtime_context: RuntimeContext;
  auth: AuthEnvelope;
  module_id: string | null;
  parent_span_id: string | null;
}

export interface AAESContext {
  request: AAESRequest;
  span: GovernedSpan;
  bus: TraceBus;
  steps_completed: StepType[];
}

export type StepStatus = "pending" | "ok" | "failed" | "skipped";

export interface AAESStep {
  step_type: StepType;
  step_id: string;
  input_hash: string;
  output_hash: string | null;
  status: StepStatus;
  error: AaesError | null;
}

export interface AAESDecision {
  allowed: boolean;
  reason_code: string;
  policy_hash: string;
  governor_auth: AuthEnvelope;
  payload: Record<string, unknown>;
}

export interface AAESAction {
  action_id: string;
  tool: string;
  args: Record<string, unknown>;
  executor_auth: AuthEnvelope;
  rollback_possible: boolean;
}

export interface AaesError {
  code: string;
  message: string;
}

export type Result<T, E = AaesError> =
  | { ok: true; value: T }
  | { ok: false; error: E };

export interface TraceBus {
  validate(event: TraceEvent, span: GovernedSpan): Result<TraceEvent>;
  append(event: TraceEvent, span: GovernedSpan): Result<TraceEvent>;
  get_events(span_id: string): TraceEvent[];
  validate_and_append(event: TraceEvent, span: GovernedSpan): Result<TraceEvent>;
  register_span(span: GovernedSpan): void;
}

export interface InvariantEngine {
  check(
    event: TraceEvent,
    span: GovernedSpan,
    prior: TraceEvent[],
  ): Result<void>;
  check_ids(
    ids: InvariantId[],
    event: TraceEvent,
    span: GovernedSpan,
    prior: TraceEvent[],
  ): Result<void>;
}

export interface PolicyEngine {
  evaluate(request: AAESRequest, context: AAESContext): Result<AAESDecision>;
}

export interface ULS {
  readonly surface_id: string;
  normalize(raw: string | Record<string, unknown>): Result<Record<string, unknown>>;
}

export interface DanielModule {
  readonly module_id: string;
  plan(context: AAESContext): Result<Record<string, unknown>>;
  execute(action: AAESAction, context: AAESContext): Result<Record<string, unknown>>;
}

export interface ModuleRegistry {
  register(module: DanielModule): void;
  get(module_id: string): DanielModule | null;
  list(): string[];
}

export interface CognitiveOrchestrator {
  execute(request: AAESRequest): Result<AAESContext>;
}

export interface TraceStore {
  save_event(event: TraceEvent): Result<void>;
  load_span(span_id: string): Result<TraceEvent[]>;
  load_trace(trace_id: string): Result<ReconstructedSpan>;
}
