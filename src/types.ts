/**
 * Mythic: AAES-OS core records
 * Engineering: AaesOsTypes
 */

export type StepStatus = "pending" | "ok" | "failed" | "skipped" | "blocked";

export interface AaesScope {
  name: string;
  resources?: string[];
}

export interface AAESRequest {
  traceId?: string;
  actorId: string;
  prompt?: string;
  payload?: unknown;
  scope?: AaesScope;
  metadata?: Record<string, unknown>;
}

export interface AaesSession {
  normalized?: NormalizedInput;
}

export interface AAESContext {
  traceId: string;
  request: AAESRequest;
  session: AaesSession;
  steps: AAESStep[];
  metadata: Record<string, unknown>;
}

export interface AAESStep {
  stepId: string;
  stepType: string;
  summary: string;
  timestamp: string;
  status: StepStatus;
  payload?: Record<string, unknown>;
  metadata?: {
    previousHash?: string;
    [key: string]: unknown;
  };
}

export interface NormalizedInput {
  intent: string;
  entities: Record<string, unknown>;
  raw: unknown;
}

export interface AAESPlanStep {
  id: string;
  kind: string;
  description: string;
}

export interface AAESPlan {
  planId: string;
  intent: string;
  steps: AAESPlanStep[];
  rationale?: string;
  score?: number;
}

export interface AAESDecision {
  selectedPlan: AAESPlan | null;
  rationale: string;
  blocked: boolean;
  blockReason?: string;
}

export interface AAESAction {
  actionId: string;
  target: string;
  operation: string;
  args: Record<string, unknown>;
}

export interface ActionResult {
  actionId: string;
  target: string;
  status: "success" | "failed" | "denied" | "skipped";
  output?: unknown;
  error?: string;
}

export interface InvariantViolation {
  code: string;
  message: string;
}

export interface InvariantResult {
  allowed: boolean;
  violations: InvariantViolation[];
}

export interface PolicyResult {
  allowed: boolean;
  reason: string;
  code?: string;
}

export interface OrchestratorResult {
  ok: boolean;
  traceId: string;
  results: ActionResult[];
  decision?: AAESDecision;
  steps: AAESStep[];
  error?: { code: string; message: string };
}

export interface AuditLogger {
  appendStep(ctx: AAESContext, step: AAESStep): void;
}

export function createStep(
  stepType: string,
  summary: string,
  payload?: Record<string, unknown>,
  metadata?: AAESStep["metadata"],
): AAESStep {
  return {
    stepId: `step_${crypto.randomUUID()}`,
    stepType,
    summary,
    timestamp: new Date().toISOString(),
    status: "ok",
    payload,
    metadata,
  };
}

export function newTraceId(): string {
  return `trace_${crypto.randomUUID()}`;
}
