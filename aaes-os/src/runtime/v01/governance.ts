/**
 * Mythic: Governance gate on Trace Bus
 * Engineering: GovernedTraceEmitter
 */

import type { Role, TraceEvent, TraceEventType } from "./types.js";
import type { TraceStore } from "./trace_store.js";

export class GovernanceViolationError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "GovernanceViolationError";
    this.code = code;
  }
}

const ROLE_PERMISSIONS: Record<Role, TraceEventType[]> = {
  USER: ["INTENT"],
  RUNTIME: ["DECISION"],
  EXECUTOR: ["EXECUTION", "RESULT"],
};

export function assertRoleCanEmit(role: Role, eventType: TraceEventType): void {
  if (!ROLE_PERMISSIONS[role].includes(eventType)) {
    throw new GovernanceViolationError(
      "AUTHORITY_VIOLATION",
      `Authority violation: ${role} cannot emit ${eventType}`,
    );
  }
}

/**
 * G1: EXECUTION requires prior DECISION.
 * G2: RESULT requires prior EXECUTION.
 * G3: DECISION requires prior INTENT.
 */
export function validateEventSequence(
  priorEvents: TraceEvent[],
  newEvent: TraceEvent,
): void {
  const spanEvents = priorEvents.filter((event) => event.span_id === newEvent.span_id);

  if (newEvent.type === "DECISION") {
    const hasIntent = spanEvents.some((event) => event.type === "INTENT");
    if (!hasIntent) {
      throw new GovernanceViolationError(
        "G3_VIOLATION",
        "G3 violation: DECISION requires prior INTENT",
      );
    }
  }

  if (newEvent.type === "EXECUTION") {
    const hasDecision = spanEvents.some((event) => event.type === "DECISION");
    if (!hasDecision) {
      throw new GovernanceViolationError(
        "G1_VIOLATION",
        "G1 violation: EXECUTION requires prior DECISION",
      );
    }
  }

  if (newEvent.type === "RESULT") {
    const hasExecution = spanEvents.some((event) => event.type === "EXECUTION");
    if (!hasExecution) {
      throw new GovernanceViolationError(
        "G2_VIOLATION",
        "G2 violation: RESULT requires prior EXECUTION",
      );
    }
  }
}

/** Single enforcement entry point — authority + causal invariants before append. */
export function emitEvent(role: Role, event: TraceEvent, store: TraceStore): void {
  assertRoleCanEmit(role, event.type);
  const prior = store.getEventsBySpan(event.span_id);
  validateEventSequence(prior, event);
  store.append(event);
}
