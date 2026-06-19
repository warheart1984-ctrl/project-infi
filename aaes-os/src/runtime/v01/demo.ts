/**
 * AAES-OS v0.1 minimal demo — valid trace + governance rejection.
 */

import { randomUUID } from "node:crypto";

import { emitEvent, GovernanceViolationError } from "./governance.js";
import { formatReconstructionSummary, reconstructSpan } from "./reconstruct.js";
import { InMemoryTraceStore } from "./trace_store.js";
import type { DecisionEvent, ExecutionEvent, IntentEvent, ResultEvent } from "./types.js";

function now(): string {
  return new Date().toISOString();
}

export function runV01Demo(): {
  validSummary: string;
  g2Rejected: boolean;
  authorityRejected: boolean;
} {
  const store = new InMemoryTraceStore();
  const span = randomUUID();

  emitEvent(
    "USER",
    {
      id: randomUUID(),
      span_id: span,
      type: "INTENT",
      timestamp: now(),
      actor: "user",
      payload: { request: "Analyze this request" },
    } satisfies IntentEvent,
    store,
  );

  emitEvent(
    "RUNTIME",
    {
      id: randomUUID(),
      span_id: span,
      type: "DECISION",
      timestamp: now(),
      actor: "runtime",
      payload: { decision: "select_analysis_workflow" },
    } satisfies DecisionEvent,
    store,
  );

  emitEvent(
    "EXECUTOR",
    {
      id: randomUUID(),
      span_id: span,
      type: "EXECUTION",
      timestamp: now(),
      actor: "executor",
      payload: { action: "run_analysis", status: "COMPLETED" },
    } satisfies ExecutionEvent,
    store,
  );

  emitEvent(
    "EXECUTOR",
    {
      id: randomUUID(),
      span_id: span,
      type: "RESULT",
      timestamp: now(),
      actor: "executor",
      payload: { outcome: { summary: "analysis output" }, status: "SUCCESS" },
    } satisfies ResultEvent,
    store,
  );

  const validSummary = formatReconstructionSummary(reconstructSpan(store, span));

  let g2Rejected = false;
  try {
    emitEvent(
      "EXECUTOR",
      {
        id: randomUUID(),
        span_id: randomUUID(),
        type: "RESULT",
        timestamp: now(),
        actor: "executor",
        payload: { outcome: {}, status: "SUCCESS" },
      } satisfies ResultEvent,
      store,
    );
  } catch (error) {
    g2Rejected =
      error instanceof GovernanceViolationError && error.code === "G2_VIOLATION";
  }

  let authorityRejected = false;
  try {
    emitEvent(
      "RUNTIME",
      {
        id: randomUUID(),
        span_id: randomUUID(),
        type: "INTENT",
        timestamp: now(),
        actor: "runtime",
        payload: { request: "fake user intent" },
      } satisfies IntentEvent,
      store,
    );
  } catch (error) {
    authorityRejected =
      error instanceof GovernanceViolationError && error.code === "AUTHORITY_VIOLATION";
  }

  return { validSummary, g2Rejected, authorityRejected };
}
