import type { ThresholdRegistry } from "../registry/threshold-registry";
import type {
  DriftSignals,
  MetricHistory,
  RecalibrationTrigger,
  Threshold,
  ValidationContext,
} from "../css2/types";

export async function detectRecalibrationTriggers(
  event: { domain?: string; metric?: string },
  driftSignals: DriftSignals,
  validation: ValidationContext,
  registry: ThresholdRegistry,
): Promise<RecalibrationTrigger[]> {
  const triggers: RecalibrationTrigger[] = [];

  const thresholds = await registry.query({
    domain: event.domain,
    metric: event.metric,
    activeOnly: true,
  });

  for (const th of thresholds) {
    if (isSystematicMisclassification(event, th, validation)) {
      triggers.push({
        thresholdId: th.id,
        reason: "systematic_misclassification",
        evidence: [event, validation],
      });
    }
    if (isLateIntervention(event, th, validation)) {
      triggers.push({
        thresholdId: th.id,
        reason: "late_intervention",
        evidence: [event, validation],
      });
    }
    if (isOverIntervention(event, th, validation)) {
      triggers.push({
        thresholdId: th.id,
        reason: "over_intervention",
        evidence: [event, validation],
      });
    }
    if (validation.operator_feedback) {
      triggers.push({
        thresholdId: th.id,
        reason: "operator_feedback",
        evidence: [event, validation],
      });
    }
  }

  if (hasStrongDriftSignal(driftSignals)) {
    const impacted =
      thresholds.length > 0
        ? thresholds
        : await registry.query({ domain: driftSignals.domain, activeOnly: true });
    for (const th of impacted) {
      triggers.push({
        thresholdId: th.id,
        reason: "drift_signal",
        evidence: [driftSignals],
      });
    }
  }

  if (isContinuityFailurePattern(validation)) {
    for (const th of thresholds) {
      triggers.push({
        thresholdId: th.id,
        reason: "failure_pattern",
        evidence: [validation],
      });
    }
  }

  return dedupeTriggers(triggers);
}

export function isSystematicMisclassification(
  _event: unknown,
  th: Threshold,
  validation: ValidationContext,
): boolean {
  if (validation.misclassified === true) return true;
  const history: MetricHistory | undefined = validation.historyForThreshold?.[th.id];
  if (!history) return false;
  const misclassifiedCount = history.values.filter((v) => v === 1).length;
  const total = history.values.length;
  return total >= 10 && misclassifiedCount / total > 0.3;
}

export function isLateIntervention(
  _event: unknown,
  th: Threshold,
  validation: ValidationContext,
): boolean {
  if (validation.late === true) return true;
  const count = validation.lateInterventionsForThreshold?.[th.id];
  return count !== undefined && count > 5;
}

export function isOverIntervention(
  _event: unknown,
  th: Threshold,
  validation: ValidationContext,
): boolean {
  if (validation.over === true) return true;
  const rate = validation.falsePositiveRateForThreshold?.[th.id];
  return rate !== undefined && rate > 0.4;
}

export function hasStrongDriftSignal(driftSignals: DriftSignals): boolean {
  if (driftSignals.strong === true) return true;
  return (
    (driftSignals.klDivergence !== undefined && driftSignals.klDivergence > 0.5) ||
    (driftSignals.meanShift !== undefined && driftSignals.meanShift > 2.0)
  );
}

export function isContinuityFailurePattern(validation: ValidationContext): boolean {
  if (validation.pattern === "failure") return true;
  return (validation.continuityFailuresLast30Days ?? 0) >= 3;
}

function dedupeTriggers(triggers: RecalibrationTrigger[]): RecalibrationTrigger[] {
  const seen = new Set<string>();
  const out: RecalibrationTrigger[] = [];
  for (const tr of triggers) {
    const key = `${tr.thresholdId}:${tr.reason}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(tr);
  }
  return out;
}
