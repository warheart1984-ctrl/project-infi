import type { ObserverProfile } from "../css2/types";
import type { Observation } from "../observer-evidence/observation";
import type { ObservationPattern } from "../css2/types";
import type { ProtoThreshold } from "../css2/types";

export interface ObserverProtectionContext {
  observer: ObserverProfile;
  event?: Observation;
  pattern?: ObservationPattern;
  protoThreshold?: ProtoThreshold;
}

export interface ObserverProtectionDecision {
  allowed: boolean;
  reasons: string[];
}

export function enforceObserverProtection(
  ctx: ObserverProtectionContext,
): ObserverProtectionDecision {
  const reasons: string[] = [];

  if (ctx.event?.description.toLowerCase().includes("divergence")) {
    // Hook: org retaliation checks would run here.
  }

  if (ctx.protoThreshold && ctx.pattern?.status === "rejected") {
    reasons.push("Systematic suppression of ProtoThresholds in rejected pattern domain");
  }

  if (ctx.observer.flags.captured) {
    reasons.push("Observer is marked as captured");
  }

  if (ctx.observer.flags.exhausted) {
    reasons.push("Observer exhaustion — protection review required");
  }

  return {
    allowed: reasons.length === 0,
    reasons,
  };
}
