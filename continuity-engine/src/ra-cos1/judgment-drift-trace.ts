import type { Id, ISOTime } from "../css2/types";
import type { JudgmentCapability } from "../judgment/capability";
import { computeJudgmentDrift } from "../judgment/drift";
import type { ObserverTraceEvent } from "./observer-trace";

/** RA-COS-1.JD.1 — judgment drift event payload. */
export interface JudgmentDriftEvent {
  id: Id;
  observerId: Id;
  previous: JudgmentCapability;
  current: JudgmentCapability;
  driftScore: number;
  contributingEvidence: unknown[];
  timestamp: ISOTime;
  triggerReasons: JudgmentDriftTriggerReason[];
}

export type JudgmentDriftTriggerReason =
  | "drift_threshold_exceeded"
  | "valuation_sharp_drop"
  | "deliberation_sharp_drop"
  | "reflection_stagnation"
  | "commitment_constitutional_divergence"
  | "crk1_legitimacy_concern";

export interface JudgmentDriftConfig {
  /** RA-COS-1.JD.2 — record when drift exceeds this (default 0.25). */
  driftThreshold: number;
  /** Sharp drop for valuation/deliberation (default 0.15 per step). */
  sharpDropThreshold: number;
  /** Reflection stagnation: max change below this over window (default 0.02). */
  reflectionStagnationMaxDelta: number;
}

export const DEFAULT_JUDGMENT_DRIFT_CONFIG: JudgmentDriftConfig = {
  driftThreshold: 0.25,
  sharpDropThreshold: 0.15,
  reflectionStagnationMaxDelta: 0.02,
};

export interface JudgmentDriftTriggerInput {
  observerId: Id;
  previous: JudgmentCapability;
  current: JudgmentCapability;
  contributingEvidence?: unknown[];
  timestamp?: ISOTime;
  crkLegitimacyConcern?: boolean;
  commitmentViolatesConstraints?: boolean;
  config?: Partial<JudgmentDriftConfig>;
}

/** RA-COS-1.JD.2 — detect whether a drift event MUST be recorded. */
export function detectJudgmentDriftTriggers(
  input: JudgmentDriftTriggerInput,
): JudgmentDriftTriggerReason[] {
  const config = { ...DEFAULT_JUDGMENT_DRIFT_CONFIG, ...input.config };
  const reasons: JudgmentDriftTriggerReason[] = [];
  const driftScore = computeJudgmentDrift(input.previous, input.current);

  if (driftScore >= config.driftThreshold) {
    reasons.push("drift_threshold_exceeded");
  }

  const valuationDrop = input.previous.valuation - input.current.valuation;
  if (valuationDrop >= config.sharpDropThreshold) {
    reasons.push("valuation_sharp_drop");
  }

  const deliberationDrop = input.previous.deliberation - input.current.deliberation;
  if (deliberationDrop >= config.sharpDropThreshold) {
    reasons.push("deliberation_sharp_drop");
  }

  const reflectionDelta = Math.abs(input.previous.reflection - input.current.reflection);
  if (reflectionDelta <= config.reflectionStagnationMaxDelta && input.current.reflection < 0.4) {
    reasons.push("reflection_stagnation");
  }

  if (input.commitmentViolatesConstraints) {
    reasons.push("commitment_constitutional_divergence");
  }

  if (input.crkLegitimacyConcern) {
    reasons.push("crk1_legitimacy_concern");
  }

  return reasons;
}

export function recordJudgmentDriftEvent(
  input: JudgmentDriftTriggerInput,
): JudgmentDriftEvent | null {
  const triggerReasons = detectJudgmentDriftTriggers(input);
  if (triggerReasons.length === 0) return null;

  const timestamp = input.timestamp ?? new Date().toISOString();
  const driftScore = computeJudgmentDrift(input.previous, input.current);

  return {
    id: `jd-event-${input.observerId}-${timestamp}`,
    observerId: input.observerId,
    previous: input.previous,
    current: input.current,
    driftScore,
    contributingEvidence: input.contributingEvidence ?? [],
    timestamp,
    triggerReasons,
  };
}

export function makeJudgmentDriftTrace(event: JudgmentDriftEvent): ObserverTraceEvent {
  return {
    id: `otrace-jd-${event.id}`,
    type: "judgment_drift",
    timestamp: event.timestamp,
    actorId: event.observerId,
    payload: event,
  };
}

export class InMemoryJudgmentDriftStore {
  private events: JudgmentDriftEvent[] = [];

  append(event: JudgmentDriftEvent): void {
    this.events.push(event);
  }

  queryByObserver(observerId: Id): JudgmentDriftEvent[] {
    return this.events.filter((e) => e.observerId === observerId);
  }

  queryAll(): JudgmentDriftEvent[] {
    return [...this.events];
  }
}
