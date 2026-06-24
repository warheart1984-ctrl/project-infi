import type { ThresholdRegistry } from "../registry/threshold-registry";
import type {
  DriftSignals,
  InvariantSet,
  RecalibrationEvent,
  RecalibrationTrigger,
  Threshold,
  ThresholdDelta,
  ValidationContext,
} from "../css2/types";
import { RecalibrationGovernanceEngine } from "../governance/governance-engine";
import { detectRecalibrationTriggers } from "./trigger-detection";

export interface RACosLoopDeps {
  registry: ThresholdRegistry;
  governance: RecalibrationGovernanceEngine;
  invariantSet: InvariantSet;
  onRejected?: (event: RecalibrationEvent) => void | Promise<void>;
  onApproved?: (event: RecalibrationEvent, threshold: Threshold) => void | Promise<void>;
}

export interface RACosEvent {
  domain?: string;
  metric?: string;
  [key: string]: unknown;
}

export async function processRACosEvent(
  deps: RACosLoopDeps,
  event: RACosEvent,
  driftSignals: DriftSignals,
  validation: ValidationContext,
): Promise<{ triggers: RecalibrationTrigger[]; events: RecalibrationEvent[] }> {
  const triggers = await detectRecalibrationTriggers(
    event,
    driftSignals,
    validation,
    deps.registry,
  );

  const events: RecalibrationEvent[] = [];

  for (const trig of triggers) {
    const th = await deps.registry.getById(trig.thresholdId);
    if (!th) continue;

    const delta: ThresholdDelta = {
      thresholdId: th.id,
      before: th,
      after: { value: proposeNewValue(th, trig) },
      rationale: `Auto-proposal based on trigger: ${trig.reason}`,
    };

    const recEvent = await deps.governance.evaluate({
      delta,
      invSet: deps.invariantSet,
      evidence: trig.evidence,
      triggerType: mapTriggerToType(trig.reason),
    });

    events.push(recEvent);

    if (recEvent.decision === "approved") {
      const updated = await deps.registry.applyDelta(
        {
          thresholdId: th.id,
          before: th,
          after: delta.after,
          rationale: delta.rationale,
          recalibrationEventId: recEvent.eventId,
        },
        recEvent.decidedBy,
      );
      await deps.onApproved?.(recEvent, updated);
    } else {
      await deps.onRejected?.(recEvent);
    }
  }

  return { triggers, events };
}

export function proposeNewValue(th: Threshold, trig: RecalibrationTrigger): unknown {
  if (typeof th.value !== "number") return th.value;
  if (trig.reason === "late_intervention") {
    return Math.max(1, th.value - 1);
  }
  if (trig.reason === "over_intervention") {
    return th.value + 1;
  }
  return th.value;
}

function mapTriggerToType(
  reason: RecalibrationTrigger["reason"],
): RecalibrationEvent["triggerType"] {
  switch (reason) {
    case "drift_signal":
      return "drift";
    case "failure_pattern":
      return "failure";
    case "operator_feedback":
      return "other";
    default:
      return "evidence";
  }
}
