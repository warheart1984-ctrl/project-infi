import type { ObserverProfile } from "../css2/types";

export interface ObserverStewardshipDecision {
  observerId: string;
  needsSupport: boolean;
  reasons: string[];
  recommendedActions: string[];
}

export function evaluateObserverStewardship(
  observer: ObserverProfile,
): ObserverStewardshipDecision {
  const reasons: string[] = [];
  const actions: string[] = [];

  if (observer.driftScore > 0.7) {
    reasons.push("High observer drift");
    actions.push("Pair with senior observer for calibration review");
  }

  if (observer.flags.captured) {
    reasons.push("Observer appears captured");
    actions.push("Route to governance review; isolate from critical decisions");
  }

  if (observer.flags.exhausted) {
    reasons.push("Observer exhaustion");
    actions.push("Reduce load; schedule recovery period");
  }

  return {
    observerId: observer.id,
    needsSupport: reasons.length > 0,
    reasons,
    recommendedActions: actions,
  };
}
