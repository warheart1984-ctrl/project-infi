import type { JudgmentCycle, JudgmentCycleDraft, JudgmentEvaluation } from "../judgment/types.js";
import { isCycleComplete } from "../judgment/payload.js";
import { computeJudgmentDriftFromProfiles } from "../judgment/analytics/drift.js";
import { evaluateJudgmentFromCycles } from "../judgment/analytics/evaluation.js";
import { inferCapabilityProfile } from "../judgment/analytics/capability.js";

export interface JudgmentGovernanceContext {
  actorId: string;
  cycles: (JudgmentCycle | JudgmentCycleDraft)[];
  priorCycleCutoffIndex?: number;
}

export interface JudgmentLegitimacyResult {
  evaluation: JudgmentEvaluation;
  driftScore: number;
  passesMinimumStandard: boolean;
  reasons: string[];
}

function splitCycles(
  cycles: (JudgmentCycle | JudgmentCycleDraft)[],
  actorId: string,
  cutoffIndex?: number,
): { prior: (JudgmentCycle | JudgmentCycleDraft)[]; current: (JudgmentCycle | JudgmentCycleDraft)[] } {
  const actorCycles = cycles.filter((c) => c.observerId === actorId);
  if (cutoffIndex === undefined || cutoffIndex <= 0) {
    const complete = actorCycles.filter((c) => isCycleComplete(c));
    if (complete.length < 2) {
      return { prior: [], current: actorCycles };
    }
    const mid = Math.floor(complete.length / 2);
    const priorIds = new Set(complete.slice(0, mid).map((c) => c.id));
    return {
      prior: actorCycles.filter((c) => priorIds.has(c.id)),
      current: actorCycles.filter((c) => !priorIds.has(c.id)),
    };
  }
  return {
    prior: actorCycles.slice(0, cutoffIndex),
    current: actorCycles.slice(cutoffIndex),
  };
}

/** JPA-1: legitimacy from cycle evidence, not raw capability vectors */
export function assessJudgmentLegitimacy(
  ctx: JudgmentGovernanceContext,
  minScore = 0.5,
  maxDrift = 0.6,
): JudgmentLegitimacyResult {
  const { prior, current } = splitCycles(ctx.cycles, ctx.actorId, ctx.priorCycleCutoffIndex);

  const evaluation = evaluateJudgmentFromCycles(current, ctx.actorId);
  const priorProfile = inferCapabilityProfile(prior, ctx.actorId);
  const currentProfile = inferCapabilityProfile(current, ctx.actorId);
  const driftScore = computeJudgmentDriftFromProfiles(priorProfile, currentProfile);

  const reasons: string[] = [];

  if (evaluation.evidenceCycleCount === 0) {
    reasons.push("No judgment cycles on record for actor — capability cannot be inferred");
  }

  if (evaluation.score < minScore) {
    reasons.push(
      `Inferred judgment score ${evaluation.score.toFixed(2)} below minimum ${minScore.toFixed(2)} (hypothesis from ${evaluation.evidenceCycleCount} cycles)`,
    );
  }

  if (driftScore > maxDrift) {
    reasons.push(
      `Judgment drift ${driftScore.toFixed(2)} exceeds maximum ${maxDrift.toFixed(2)}`,
    );
  }

  const passesMinimumStandard =
    evaluation.evidenceCycleCount > 0 &&
    evaluation.score >= minScore &&
    driftScore <= maxDrift;

  return {
    evaluation,
    driftScore,
    passesMinimumStandard,
    reasons,
  };
}
