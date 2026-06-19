/**
 * Mythic: Span reconstruction
 * Engineering: GovernedSpanReconstructor
 */

import type { TraceStore } from "./trace_store.js";
import type {
  DecisionEvent,
  ExecutionEvent,
  IntentEvent,
  Reconstruction,
  ResultEvent,
} from "./types.js";

export function reconstructSpan(store: TraceStore, span_id: string): Reconstruction {
  const events = store
    .getEventsBySpan(span_id)
    .sort((left, right) => left.timestamp.localeCompare(right.timestamp));

  return {
    intent: events.find((event) => event.type === "INTENT") as IntentEvent | undefined,
    decision: events.find((event) => event.type === "DECISION") as DecisionEvent | undefined,
    execution: events.filter((event) => event.type === "EXECUTION") as ExecutionEvent[],
    result: events.find((event) => event.type === "RESULT") as ResultEvent | undefined,
  };
}

export function formatReconstructionSummary(recon: Reconstruction): string {
  const lines = ["VALID TRACE", ""];
  lines.push(`Intent:\n${recon.intent?.payload.request ?? "(missing)"}`);
  lines.push(`Decision:\n${recon.decision?.payload.decision ?? "(missing)"}`);
  const actions = recon.execution.map((row) => row.payload.action).join(", ");
  lines.push(`Execution:\n${actions || "(missing)"}`);
  const outcome =
    recon.result?.payload.outcome &&
    typeof recon.result.payload.outcome === "object" &&
    recon.result.payload.outcome !== null &&
    "summary" in recon.result.payload.outcome
      ? String((recon.result.payload.outcome as { summary: unknown }).summary)
      : JSON.stringify(recon.result?.payload.outcome ?? "(missing)");
  lines.push(`Result:\n${outcome}`);
  return lines.join("\n\n");
}
