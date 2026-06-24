import type { ObserverProfile, ObserverStage } from "./types";

const STAGE_ORDER: ObserverStage[] = ["person", "observer", "senior_observer", "steward"];

export function advanceObserverStage(observer: ObserverProfile): ObserverProfile {
  const idx = STAGE_ORDER.indexOf(observer.stage);
  if (idx < 0 || idx >= STAGE_ORDER.length - 1) return observer;
  return { ...observer, stage: STAGE_ORDER[idx + 1]! };
}

export function runObserverLifecycle(observer: ObserverProfile): ObserverProfile {
  const avg =
    (observer.capabilities.perception +
      observer.capabilities.interpretation +
      observer.capabilities.hypothesis +
      observer.capabilities.judgment +
      observer.capabilities.stewardship) /
    5;

  if (avg >= 0.5 && observer.stage === "person") {
    return advanceObserverStage(observer);
  }
  if (avg >= 0.65 && observer.stage === "observer") {
    return advanceObserverStage(observer);
  }
  if (avg >= 0.75 && observer.stage === "senior_observer") {
    return advanceObserverStage(observer);
  }
  return observer;
}

export function evaluateObserverCapabilities(observer: ObserverProfile): Record<string, number> {
  return { ...observer.capabilities };
}
