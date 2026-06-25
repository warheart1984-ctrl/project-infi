import type { CyclePayload, JudgmentCycle, JudgmentCycleDraft } from "./types.js";

export function emptyPayload(): CyclePayload {
  return { summary: "", eventIds: [] };
}

export function isPayloadFilled(payload: CyclePayload): boolean {
  return Boolean(payload.summary?.trim()) || (payload.eventIds?.length ?? 0) > 0;
}

export function createEmptyDraft(
  id: string,
  observerId: string,
  timestamp: string,
): JudgmentCycleDraft {
  return {
    id,
    observerId,
    timestamp,
    startedAt: timestamp,
    status: "OPEN",
    observation: emptyPayload(),
    interpretation: emptyPayload(),
    valuation: emptyPayload(),
    decision: emptyPayload(),
    context: emptyPayload(),
    outcome: emptyPayload(),
    feedback: emptyPayload(),
    reflection: emptyPayload(),
    relatedThresholdIds: [],
    relatedDeltaIds: [],
    tags: [],
    buildsOn: [],
  };
}

export function isDraftComplete(draft: JudgmentCycleDraft): boolean {
  return (
    isPayloadFilled(draft.observation) &&
    isPayloadFilled(draft.interpretation) &&
    isPayloadFilled(draft.valuation) &&
    isPayloadFilled(draft.decision) &&
    isPayloadFilled(draft.outcome) &&
    isPayloadFilled(draft.feedback) &&
    isPayloadFilled(draft.reflection)
  );
}

export function finalizeDraft(draft: JudgmentCycleDraft): JudgmentCycle {
  const { status: _s, startedAt: _a, buildsOn, ...cycle } = draft;
  return {
    ...cycle,
    timestamp: draft.timestamp,
    context: {
      ...draft.context,
      buildsOn,
    },
  };
}

export function isLedgerCycle(cycle: JudgmentCycle | JudgmentCycleDraft): cycle is JudgmentCycle {
  return !("status" in cycle);
}

export function isCycleComplete(cycle: JudgmentCycle | JudgmentCycleDraft): boolean {
  if ("status" in cycle) return cycle.status === "COMPLETE";
  return true;
}
