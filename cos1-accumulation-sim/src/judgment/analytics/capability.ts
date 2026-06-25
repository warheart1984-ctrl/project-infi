import type {
  JudgmentCapabilityProfile,
  JudgmentCycle,
  JudgmentCycleDraft,
  CycleLike,
} from "../types.js";
import { isCycleComplete, isPayloadFilled } from "../payload.js";

const DIMENSION_KEYS = [
  "perception",
  "interpretation",
  "valuation",
  "deliberation",
  "commitment",
  "reflection",
] as const;

function clamp01(n: number): number {
  return Math.min(1, Math.max(0, n));
}

function buildsOn(cycle: CycleLike): string[] {
  if ("buildsOn" in cycle && Array.isArray(cycle.buildsOn)) return cycle.buildsOn;
  const ctx = cycle.context?.buildsOn;
  return Array.isArray(ctx) ? (ctx as string[]) : [];
}

function scoreCycleDimensions(
  cycle: CycleLike,
): Omit<JudgmentCapabilityProfile, "evidenceCycles" | "score"> {
  const obs = cycle.observation ?? {};
  const interp = cycle.interpretation ?? {};
  const hasAnchor = Boolean(obs.phenomenonAnchor);
  const external = obs.origin === "PLA" || obs.fromExposure === false;

  const perception = clamp01(
    (hasAnchor ? 0.5 : 0.2) + (external ? 0.4 : 0.1) + (isPayloadFilled(obs) ? 0.1 : 0),
  );

  const accType = String(interp.accumulationType ?? "NONE");
  const interpretation = clamp01(
    (accType === "A2" || accType === "A3" || accType === "A4" ? 0.6 : 0.35) +
      (isPayloadFilled(cycle.interpretation) ? 0.25 : 0),
  );

  const valuation = clamp01(
    (isPayloadFilled(cycle.valuation) ? 0.5 : 0) +
      (String(interp.targetsLayer ?? "").length > 0 ? 0.3 : 0) +
      (isCycleComplete(cycle) ? 0.2 : 0),
  );

  const deliberation = clamp01(
    Math.min(1, buildsOn(cycle).length * 0.25 + (isPayloadFilled(cycle.interpretation) ? 0.35 : 0)),
  );

  const commitment = clamp01(
    isPayloadFilled(cycle.decision)
      ? 0.7 + (buildsOn(cycle).length > 0 ? 0.2 : 0)
      : 0.1,
  );

  const reflection = clamp01(
    (isPayloadFilled(cycle.reflection) ? 0.6 : 0) +
      (isPayloadFilled(cycle.outcome) ? 0.2 : 0) +
      (isPayloadFilled(cycle.feedback) ? 0.15 : 0) +
      (isCycleComplete(cycle) ? 0.05 : 0),
  );

  return { perception, interpretation, valuation, deliberation, commitment, reflection };
}

function averageDimension(
  cycles: CycleLike[],
  key: (typeof DIMENSION_KEYS)[number],
): number {
  if (cycles.length === 0) return 0;
  const sum = cycles.reduce((acc, c) => acc + scoreCycleDimensions(c)[key], 0);
  return clamp01(sum / cycles.length);
}

export function inferCapabilityProfile(
  cycles: CycleLike[],
  observerId: string,
  options: { minComplete?: number; includeOpen?: boolean } = {},
): JudgmentCapabilityProfile {
  const { minComplete = 1, includeOpen = false } = options;
  const relevant = cycles.filter((c) => {
    if (c.observerId !== observerId) return false;
    if (isCycleComplete(c)) return true;
    return includeOpen;
  });

  const complete = relevant.filter((c) => isCycleComplete(c));
  let evidence =
    complete.length >= minComplete ? complete : includeOpen ? relevant : complete;

  if (evidence.length === 0) {
    evidence = cycles.filter(
      (c) => c.observerId === observerId && "status" in c && c.status === "OPEN",
    );
  }

  if (evidence.length === 0) {
    return {
      perception: 0,
      interpretation: 0,
      valuation: 0,
      deliberation: 0,
      commitment: 0,
      reflection: 0,
      evidenceCycles: [],
      score: 0,
    };
  }

  const perception = averageDimension(evidence, "perception");
  const interpretation = averageDimension(evidence, "interpretation");
  const valuation = averageDimension(evidence, "valuation");
  const deliberation = averageDimension(evidence, "deliberation");
  const commitment = averageDimension(evidence, "commitment");
  const reflection = averageDimension(evidence, "reflection");

  const score = clamp01(
    (perception + interpretation + valuation + deliberation + commitment + reflection) / 6,
  );

  return {
    perception,
    interpretation,
    valuation,
    deliberation,
    commitment,
    reflection,
    evidenceCycles: evidence.map((c) => c.id),
    score,
  };
}

export function inferAllCapabilityProfiles(
  cycles: CycleLike[],
): Record<string, JudgmentCapabilityProfile> {
  const observers = new Set(cycles.map((c) => c.observerId));
  const profiles: Record<string, JudgmentCapabilityProfile> = {};
  for (const observerId of observers) {
    profiles[observerId] = inferCapabilityProfile(cycles, observerId);
  }
  return profiles;
}
