import type { ObserverProfile } from "../css2/types";

export function computeObserverDrift(
  _observer: ObserverProfile,
  referenceBeliefs: string[],
  currentBeliefs: string[],
): number {
  const refSet = new Set(referenceBeliefs);
  const curSet = new Set(currentBeliefs);

  const intersection = [...refSet].filter((b) => curSet.has(b)).length;
  const union = new Set([...refSet, ...curSet]).size;

  const jaccard = union === 0 ? 0 : intersection / union;
  const drift = 1 - jaccard;

  return Math.min(1, Math.max(0, drift));
}
