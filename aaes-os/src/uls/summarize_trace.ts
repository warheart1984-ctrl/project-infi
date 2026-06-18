/**
 * Mythic: Unified Language Surface — trace summarizer
 * Engineering: summarizeTrace
 */

import type { AAESStep } from "../types.js";

export interface TraceSummary {
  stepCount: number;
  statuses: Record<string, number>;
  narrative: string;
}

/** Produce a human-readable summary of an execution trace. */
export function summarizeTrace(steps: AAESStep[]): TraceSummary {
  const statuses: Record<string, number> = {};
  for (const step of steps) {
    statuses[step.status] = (statuses[step.status] ?? 0) + 1;
  }

  const lines = steps.map(
    (s, i) => `${i + 1}. [${s.stepType}] ${s.summary} (${s.status})`,
  );

  const narrative =
    steps.length === 0
      ? "No steps recorded."
      : `Trace with ${steps.length} step(s):\n${lines.join("\n")}`;

  return {
    stepCount: steps.length,
    statuses,
    narrative,
  };
}
