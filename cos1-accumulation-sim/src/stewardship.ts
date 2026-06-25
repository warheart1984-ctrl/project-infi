import type { PlayerProfile } from "./wck.js";

export interface StewardCandidateSignal {
  plaDepth: number;
  laDepth: number;
  saEvidence: number;
  reconstructability: number;
  validationRate: number;
  driftImpact: number;
}

export function computeStewardScore(s: StewardCandidateSignal): number {
  return (
    0.2 * s.plaDepth +
    0.25 * s.laDepth +
    0.25 * s.saEvidence +
    0.15 * s.reconstructability +
    0.15 * s.validationRate -
    0.2 * s.driftImpact
  );
}

export function evaluateStewardPromotion(
  player: PlayerProfile,
  signals: StewardCandidateSignal,
  threshold = 0.7,
): PlayerProfile {
  const score = computeStewardScore(signals);
  if (score >= threshold && !player.roles.includes("STEWARD")) {
    return {
      ...player,
      stewardshipScore: score,
      roles: [...player.roles, "STEWARD"],
    };
  }
  return { ...player, stewardshipScore: score };
}

export function buildStewardSignals(
  plaCount: number,
  laCount: number,
  saCount: number,
  plaDepth: number,
  laDepth: number,
  reconstructabilityScore: number,
  validatedChanges: number,
  totalChanges: number,
  driftAggregatePSD: number | null,
): StewardCandidateSignal {
  const total = Math.max(plaCount + laCount + saCount, 1);
  return {
    plaDepth: plaCount > 0 ? plaDepth : 0,
    laDepth: laCount > 0 ? laDepth : 0,
    saEvidence: Math.min(1, saCount / total),
    reconstructability: reconstructabilityScore,
    validationRate: totalChanges === 0 ? 0 : validatedChanges / totalChanges,
    driftImpact: Math.min(1, driftAggregatePSD ?? 0),
  };
}
