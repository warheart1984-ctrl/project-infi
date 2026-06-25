import {
  AccumulationOrigin,
  AccumulationScore,
  ContinuityInterpretation,
  InvariantHealth,
  JPSSContributionEvent,
  LAMetrics,
  ReconstructabilityMetrics,
  SAMetrics,
  ThresholdConfig,
  ThresholdStatus,
} from "./domain.js";

const STRUCTURAL_TYPES = new Set(["A2", "A3", "A4"]);

export const DEFAULT_THRESHOLDS: ThresholdConfig = {
  plt1MinEvents: 3,
  plt1MinActors: 2,
  mat3MinLaEvents: 3,
  mat3MinLaActors: 2,
  k4Threshold: 0.7,
  k3IntegrationMin: 0.5,
};

export function eventsByOrigin(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
  origin: AccumulationOrigin,
): JPSSContributionEvent[] {
  return events.filter((e) => origins[e.id] === origin);
}

export function computeStratumCounts(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
): { pla: number; la: number; sa: number } {
  return {
    pla: eventsByOrigin(events, origins, "PLA").length,
    la: eventsByOrigin(events, origins, "LA").length,
    sa: eventsByOrigin(events, origins, "SA").length,
  };
}

/** CE-2: A(t) = f(PLA, LA, SA) — reality pressure, framework growth, governance */
export function computeAccumulationScore(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
): AccumulationScore {
  const strata = computeStratumCounts(events, origins);
  const value =
    0.35 * strata.pla + 0.45 * strata.la + 0.2 * strata.sa;
  return { value, strata };
}

export function computeLAMetrics(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
): LAMetrics {
  const laEvents = eventsByOrigin(events, origins, "LA");
  const laCount = laEvents.length;
  const laActors = new Set(laEvents.map((e) => e.actor)).size;
  const structural = laEvents.filter((e) => STRUCTURAL_TYPES.has(e.accumulationType));
  const laDepth = laCount === 0 ? 0 : structural.length / laCount;
  return { laCount, laActors, laDepth };
}

export function computeSAMetrics(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
): SAMetrics {
  const saEvents = eventsByOrigin(events, origins, "SA");
  return {
    saCount: saEvents.length,
    saActors: new Set(saEvents.map((e) => e.actor)).size,
  };
}

/** PLA events internalized when an LA event buildsOn them */
export function computePlaToLaIntegrationRate(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
): number {
  const plaIds = new Set(
    eventsByOrigin(events, origins, "PLA").map((e) => e.id),
  );
  if (plaIds.size === 0) return 0;

  const integrated = new Set<string>();
  for (const e of eventsByOrigin(events, origins, "LA")) {
    for (const id of e.buildsOn) {
      if (plaIds.has(id)) integrated.add(id);
    }
  }
  return integrated.size / plaIds.size;
}

export function evaluatePLT1(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
  config: ThresholdConfig = DEFAULT_THRESHOLDS,
): boolean {
  const plaEvents = eventsByOrigin(events, origins, "PLA");
  const actors = new Set(plaEvents.map((e) => e.actor));
  const hasStructural = plaEvents.some((e) =>
    e.accumulationType === "A2" || e.accumulationType === "A3",
  );
  return (
    plaEvents.length >= config.plt1MinEvents &&
    actors.size >= config.plt1MinActors &&
    hasStructural
  );
}

/** CSS-2 MAT-3: LA-focused lineage compounding */
export function evaluateMAT3LA(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
  config: ThresholdConfig = DEFAULT_THRESHOLDS,
): boolean {
  const laEvents = eventsByOrigin(events, origins, "LA");
  const actors = new Set(laEvents.map((e) => e.actor));
  const hasStructural = laEvents.some((e) => STRUCTURAL_TYPES.has(e.accumulationType));
  return (
    laEvents.length >= config.mat3MinLaEvents &&
    actors.size >= config.mat3MinLaActors &&
    hasStructural
  );
}

export function interpretContinuity(
  plaCount: number,
  laCount: number,
  integrationRate: number,
): ContinuityInterpretation {
  if (plaCount === 0 && laCount === 0) return "nascent";
  if (plaCount >= 1 && integrationRate >= 0.5) return "listening";
  if (plaCount >= 1 && integrationRate < 0.5) return "under-listening";
  if (plaCount === 0 && laCount >= 2) return "self-referential";
  return "nascent";
}

export function evaluateInvariantHealth(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
  reconstructability: ReconstructabilityMetrics,
  integrationRate: number,
  config: ThresholdConfig = DEFAULT_THRESHOLDS,
): InvariantHealth {
  const laEvents = eventsByOrigin(events, origins, "LA");
  const saEvents = eventsByOrigin(events, origins, "SA");
  const plaEvents = eventsByOrigin(events, origins, "PLA");

  const laStructural = laEvents.some((e) => STRUCTURAL_TYPES.has(e.accumulationType));
  const plaStructural = plaEvents.some((e) => STRUCTURAL_TYPES.has(e.accumulationType));

  const k1IdentityCoherence =
    saEvents.length === 0 ||
    laEvents.every((e) => e.lineageCompatible !== false);

  const k2GenerativeGrammar = laStructural || plaStructural;

  const k3Integrability =
    plaEvents.length === 0 || integrationRate >= config.k3IntegrationMin;

  const saCompression = saEvents.length > 0 ? 0.1 * saEvents.length : 0;
  const adjustedCost = Math.max(
    0,
    reconstructability.reconstructionCost - saCompression,
  );
  const k4Reconstructability = adjustedCost <= reconstructability.reconstructionThreshold;

  return {
    k1IdentityCoherence,
    k2GenerativeGrammar,
    k3Integrability,
    k4Reconstructability,
  };
}

export function evaluateThresholds(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
  stewardQualified: boolean,
  config: ThresholdConfig = DEFAULT_THRESHOLDS,
): ThresholdStatus {
  return {
    plt1: evaluatePLT1(events, origins, config),
    mat3: evaluateMAT3LA(events, origins, config),
    stewardEmergence: stewardQualified,
  };
}
