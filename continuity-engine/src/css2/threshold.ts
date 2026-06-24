import type { Comparator, Threshold, ThresholdCreateInput, ThresholdDelta } from "./types";
import { mergeThreshold } from "./types";

export function createThreshold(input: ThresholdCreateInput): Threshold {
  const now = new Date().toISOString();
  const actor = input.createdBy;
  return {
    ...input,
    version: 1,
    active: true,
    createdAt: now,
    lastUpdatedAt: now,
    lastUpdatedBy: input.lastUpdatedBy ?? actor,
  };
}

export function applyThreshold(
  threshold: Threshold,
  observed: unknown,
): "normal" | "concerning" | "intervention" {
  const { comparator, value } = threshold;
  if (typeof value !== "number" || typeof observed !== "number") {
    return "normal";
  }
  switch (comparator) {
    case ">":
      return observed > value ? "intervention" : "normal";
    case ">=":
      return observed >= value ? "intervention" : "normal";
    case "<":
      return observed < value ? "intervention" : "normal";
    case "<=":
      return observed <= value ? "intervention" : "normal";
    case "==":
      return observed === value ? "intervention" : "normal";
    case "!=":
      return observed !== value ? "intervention" : "normal";
    default:
      return "normal";
  }
}

export function applyThresholdDelta(
  delta: ThresholdDelta,
  actorId: string,
): Threshold {
  const nextVersion = delta.before.version + 1;
  const now = new Date().toISOString();
  return mergeThreshold(delta.before, {
    ...delta.after,
    version: nextVersion,
    lastUpdatedAt: now,
    lastUpdatedBy: actorId,
  });
}

export function validateComparator(c: string): c is Comparator {
  return [">", ">=", "<", "<=", "==", "!=", "in", "out"].includes(c);
}
