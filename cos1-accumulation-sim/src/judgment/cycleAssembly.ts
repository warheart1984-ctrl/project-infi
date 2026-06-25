import type { JPSSContributionEvent } from "../domain.js";
import type { CyclePayload, JudgmentCycle, JudgmentCycleDraft } from "./types.js";
import {
  createEmptyDraft,
  finalizeDraft,
  isDraftComplete,
} from "./payload.js";

function mergePayload(existing: CyclePayload, next: CyclePayload): CyclePayload {
  return {
    ...existing,
    ...next,
    summary: next.summary || existing.summary,
    eventIds: [...(existing.eventIds ?? []), ...(next.eventIds ?? [])],
    timestamp: next.timestamp ?? existing.timestamp,
  };
}

function payloadFromEvent(
  ev: JPSSContributionEvent,
  summary: string,
  extra: Record<string, unknown> = {},
): CyclePayload {
  return {
    summary,
    eventIds: [ev.id],
    timestamp: ev.timestamp,
    accumulationType: ev.accumulationType,
    targetsLayer: ev.targetsLayer,
    origin: ev.origin,
    mode: ev.mode,
    fromExposure: ev.fromExposure,
    phenomenonAnchor: ev.phenomenonAnchor ?? null,
    ...extra,
  };
}

export { createEmptyDraft };

export interface CycleAssemblyResult {
  drafts: JudgmentCycleDraft[];
  ledgerCycles: JudgmentCycle[];
}

export function advanceCycleFromEvent(
  drafts: JudgmentCycleDraft[],
  ledgerCycles: JudgmentCycle[],
  ev: JPSSContributionEvent,
): CycleAssemblyResult {
  const openIdx = drafts.findIndex(
    (c) => c.observerId === ev.actor && c.status === "OPEN",
  );
  let draft: JudgmentCycleDraft =
    openIdx >= 0
      ? { ...drafts[openIdx] }
      : createEmptyDraft(`JC_${ev.id}`, ev.actor, ev.timestamp);

  draft.context = mergePayload(draft.context, {
    summary: "assembly context",
    targetsLayer: ev.targetsLayer,
    origin: ev.origin,
  });

  switch (ev.mode) {
    case "OBSERVATION":
      draft.observation = mergePayload(
        draft.observation,
        payloadFromEvent(ev, ev.phenomenonAnchor ?? "observation recorded"),
      );
      break;
    case "INTERPRETATION":
      draft.interpretation = mergePayload(
        draft.interpretation,
        payloadFromEvent(ev, `interpretation ${ev.accumulationType} on ${ev.targetsLayer}`),
      );
      draft.valuation = mergePayload(
        draft.valuation,
        payloadFromEvent(ev, `valued layer: ${ev.targetsLayer}`, {
          valuationNote: "layer priority from interpretation event",
        }),
      );
      break;
    case "INTEGRATION":
      draft.decision = mergePayload(
        draft.decision,
        payloadFromEvent(ev, "commitment / integration", {
          type: ev.buildsOn.some((id) => id.startsWith("WC-"))
            ? "threshold_recalibration"
            : "policy",
          buildsOn: ev.buildsOn,
          thresholdId: ev.buildsOn.find((id) => !id.startsWith("INT_")),
        }),
      );
      if (draft.decision.type === "threshold_recalibration" && draft.decision.thresholdId) {
        draft.relatedDeltaIds = [
          ...new Set([...(draft.relatedDeltaIds ?? []), String(draft.decision.thresholdId)]),
        ];
      }
      break;
    case "VALIDATION":
      draft.outcome = mergePayload(
        draft.outcome,
        payloadFromEvent(ev, "outcome from validation", { buildsOn: ev.buildsOn }),
      );
      draft.feedback = mergePayload(
        draft.feedback,
        payloadFromEvent(ev, "feedback signals from validation", {
          validationMode: true,
        }),
      );
      draft.reflection = mergePayload(
        draft.reflection,
        payloadFromEvent(ev, "reflection / recalibration"),
      );
      break;
    default:
      break;
  }

  if (ev.buildsOn.length > 0) {
    draft.buildsOn = [...new Set([...draft.buildsOn, ...ev.buildsOn])];
  }

  draft.timestamp = ev.timestamp;

  let nextDrafts = [...drafts];
  let nextLedger = [...ledgerCycles];

  if (isDraftComplete(draft)) {
    draft.status = "COMPLETE";
    const finalized = finalizeDraft(draft);
    nextLedger = appendIfNew(nextLedger, finalized);
    if (openIdx >= 0) {
      nextDrafts = drafts.filter((_, i) => i !== openIdx);
    }
  } else if (openIdx >= 0) {
    nextDrafts[openIdx] = draft;
  } else {
    nextDrafts = [...drafts, draft];
  }

  return { drafts: nextDrafts, ledgerCycles: nextLedger };
}

function appendIfNew(ledger: JudgmentCycle[], cycle: JudgmentCycle): JudgmentCycle[] {
  if (ledger.some((c) => c.id === cycle.id)) return ledger;
  return [...ledger, cycle];
}

export function rebuildCyclesFromEvents(
  events: JPSSContributionEvent[],
): { drafts: JudgmentCycleDraft[]; ledgerCycles: JudgmentCycle[] } {
  return events.reduce(
    (acc, ev) => advanceCycleFromEvent(acc.drafts, acc.ledgerCycles, ev),
    { drafts: [] as JudgmentCycleDraft[], ledgerCycles: [] as JudgmentCycle[] },
  );
}

export function allCyclesForAnalytics(
  ledgerCycles: JudgmentCycle[],
  drafts: JudgmentCycleDraft[],
): (JudgmentCycle | JudgmentCycleDraft)[] {
  return [...ledgerCycles, ...drafts];
}
