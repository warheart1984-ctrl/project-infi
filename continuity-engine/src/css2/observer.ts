import type { Id, ISOTime, ObserverProfile, ObserverStage } from "./types";

export function createObserverProfile(
  id: Id,
  name: string,
  stage: ObserverStage = "person",
): ObserverProfile {
  return {
    id,
    name,
    stage,
    joinedAt: new Date().toISOString(),
    capabilities: {
      perception: 0.2,
      interpretation: 0.2,
      hypothesis: 0.2,
      judgment: 0.2,
      stewardship: 0.2,
    },
    driftScore: 0,
    flags: {},
  };
}

export function updateObserverDrift(observer: ObserverProfile, driftScore: number): ObserverProfile {
  return {
    ...observer,
    driftScore: Math.min(1, Math.max(0, driftScore)),
    flags: {
      ...observer.flags,
      fragmented: driftScore > 0.8 ? true : observer.flags.fragmented,
    },
  };
}

export function markObserverFlag(
  observer: ObserverProfile,
  flag: keyof ObserverProfile["flags"],
  value = true,
): ObserverProfile {
  return {
    ...observer,
    flags: { ...observer.flags, [flag]: value },
  };
}
