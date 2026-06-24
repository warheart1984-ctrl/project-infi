import { mergeThreshold } from "../css2/types";
import type { Threshold, ThresholdDelta } from "../css2/types";

export interface ThresholdFieldChange {
  field: keyof Threshold;
  before: unknown;
  after: unknown;
}

export interface ThresholdDeltaDiff {
  thresholdId: string;
  changes: ThresholdFieldChange[];
  rationale: string;
}

const DIFF_FIELDS: (keyof Threshold)[] = [
  "name",
  "domain",
  "metric",
  "comparator",
  "value",
  "unit",
  "context",
  "intent",
  "active",
];

export function diffThresholdDelta(delta: ThresholdDelta): ThresholdDeltaDiff {
  const after = mergeThreshold(delta.before, delta.after);
  const changes: ThresholdFieldChange[] = [];

  for (const field of DIFF_FIELDS) {
    const beforeVal = delta.before[field];
    const afterVal = after[field];
    if (JSON.stringify(beforeVal) !== JSON.stringify(afterVal)) {
      changes.push({ field, before: beforeVal, after: afterVal });
    }
  }

  return {
    thresholdId: delta.thresholdId,
    changes,
    rationale: delta.rationale,
  };
}
