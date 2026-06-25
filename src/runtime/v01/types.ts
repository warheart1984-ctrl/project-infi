/**
 * AAES-OS v0.1 — governed span trace contracts.
 * Mythic: Trace Bus spine
 * Engineering: GovernedTraceEventModel
 */

export type TraceEventType = "INTENT" | "DECISION" | "EXECUTION" | "RESULT";

export type Role = "USER" | "RUNTIME" | "EXECUTOR";

export interface TraceEventBase {
  id: string;
  span_id: string;
  type: TraceEventType;
  timestamp: string;
  actor: string;
  payload: unknown;
}

export interface IntentEvent extends TraceEventBase {
  type: "INTENT";
  payload: {
    request: string;
    metadata?: unknown;
  };
}

export interface DecisionEvent extends TraceEventBase {
  type: "DECISION";
  payload: {
    decision: string;
    rationale?: string;
  };
}

export interface ExecutionEvent extends TraceEventBase {
  type: "EXECUTION";
  payload: {
    action: string;
    status: "STARTED" | "COMPLETED" | "FAILED";
    metadata?: unknown;
  };
}

export interface ResultEvent extends TraceEventBase {
  type: "RESULT";
  payload: {
    outcome: unknown;
    status: "SUCCESS" | "ERROR";
  };
}

export type TraceEvent =
  | IntentEvent
  | DecisionEvent
  | ExecutionEvent
  | ResultEvent;

export interface Reconstruction {
  intent?: IntentEvent;
  decision?: DecisionEvent;
  execution: ExecutionEvent[];
  result?: ResultEvent;
}
