import {
  ValidationContext,
  DriftSignals,
  Invariant,
  ReconstructabilityMetrics,
  ContinuityMetrics,
  EpistemicMetrics,
  EpistemicBehaviorProfile,
  JPSSContributionEvent,
  AccumulationOrigin,
  LedgerEntry,
  PLAMetrics,
} from "./domain.js";
import {
  computeAccumulationScore,
  computeLAMetrics,
  computeSAMetrics,
  evaluateInvariantHealth,
  evaluateMAT3LA,
  evaluatePLT1,
  evaluateThresholds,
  interpretContinuity,
} from "./ce2.js";
import {
  classifyEvents,
  computeCouplingStrength,
  computeGravityField,
  computePLAMetrics as computePLAAccumulationMetrics,
  evaluateStewardCandidates,
  hasStewardEmergence,
} from "./pla.js";

export function logistic(x: number): number {
  return 1 / (1 + Math.exp(-x));
}

export function updateInvariantWeight(
  inv: Invariant,
  evidenceScore: number,
  learningRate: number,
): Invariant {
  const w = Math.min(Math.max(inv.weight, 1e-6), 1 - 1e-6);
  const logit = Math.log(w / (1 - w));
  const updatedLogit = logit + learningRate * inv.impact * evidenceScore;
  const newW = logistic(updatedLogit);
  return { ...inv, weight: newW };
}

export function validateVAS1(ctx: ValidationContext): {
  passed: boolean;
  criteriaPassed: string[];
} {
  const criteria = [
    { name: "predictiveAccuracy", pass: ctx.predictiveAccuracyDelta > 0 },
    { name: "explanatoryCompression", pass: ctx.explanatoryCompressionDelta > 0 },
    { name: "crossDomainConvergence", pass: ctx.crossDomainConvergence >= 0.5 },
    { name: "operationalOutcome", pass: ctx.operationalOutcomeDelta > 0 },
    { name: "critiqueStability", pass: ctx.critiqueStability >= 0.5 },
  ];
  const passedNames = criteria.filter((c) => c.pass).map((c) => c.name);
  return { passed: passedNames.length >= 3, criteriaPassed: passedNames };
}

export function computeDriftSignals(
  samples: { metric: string; value: number }[],
  baseline: number,
): DriftSignals {
  const avg = (metric: string) => {
    const vals = samples.filter((s) => s.metric === metric).map((s) => s.value);
    if (!vals.length) return 0;
    return vals.reduce((a, b) => a + b, 0) / vals.length;
  };

  const predictiveDivergence = Math.max(0, baseline - avg("predictiveAccuracy"));
  const explanatoryInflation = Math.max(0, avg("patchCount") - baseline);
  const convergenceFailure = Math.max(0, baseline - avg("crossDomainConvergence"));
  const operationalUnderperformance = Math.max(0, baseline - avg("operationalOutcome"));
  const loadSpike = Math.max(0, avg("stewardLoad") - baseline);

  const PSD =
    0.25 * predictiveDivergence +
    0.2 * explanatoryInflation +
    0.2 * convergenceFailure +
    0.2 * operationalUnderperformance +
    0.15 * loadSpike;

  return {
    predictiveDivergence,
    explanatoryInflation,
    convergenceFailure,
    operationalUnderperformance,
    loadSpike,
    aggregatePSD: PSD,
  };
}

export function deriveEpistemicProfile(
  metrics: Omit<EpistemicMetrics, "profile">,
): EpistemicBehaviorProfile {
  const total =
    metrics.observationCount +
    metrics.interpretationCount +
    metrics.integrationCount +
    metrics.validationCount;
  if (total === 0) return "nascent";

  if (
    metrics.externalObservationCount >= 2 &&
    metrics.observationCount >= metrics.interpretationCount * 0.5
  ) {
    return "instrument";
  }
  if (
    metrics.interpretationCount > metrics.observationCount * 2 &&
    metrics.validationCount < metrics.interpretationCount * 0.3
  ) {
    return "doctrine";
  }
  if (metrics.observationCount > 0 && metrics.interpretationCount > 0) {
    return "framework";
  }
  return "nascent";
}

export function computeEpistemicMetrics(events: JPSSContributionEvent[]): EpistemicMetrics {
  const obs = events.filter((e) => e.mode === "OBSERVATION");
  const interp = events.filter((e) => e.mode === "INTERPRETATION");
  const integ = events.filter((e) => e.mode === "INTEGRATION");
  const valid = events.filter((e) => e.mode === "VALIDATION");

  const observationCount = obs.length;
  const interpretationCount = interp.length;
  const integrationCount = integ.length;
  const validationCount = valid.length;

  const obsToInterpRatio =
    interpretationCount === 0 ? 0 : observationCount / interpretationCount;

  const interpToValidationRatio =
    validationCount === 0 ? 0 : interpretationCount / validationCount;

  const externalObservationCount = obs.filter((e) => !e.fromExposure).length;

  const base = {
    observationCount,
    interpretationCount,
    integrationCount,
    validationCount,
    obsToInterpRatio,
    interpToValidationRatio,
    externalObservationCount,
  };

  return {
    ...base,
    profile: deriveEpistemicProfile(base),
  };
}

export function computeReconstructability(
  events: JPSSContributionEvent[],
): ReconstructabilityMetrics {
  const conceptCount = events.length;
  const baseCost = Math.min(1, conceptCount / 50);
  const threshold = 0.7;
  return {
    reconstructionCost: baseCost,
    reconstructionThreshold: threshold,
    k4Satisfied: baseCost <= threshold,
  };
}

export function computeInstrumentalityIndex(
  quality: Pick<PLAMetrics, "clustering" | "crossDomainRecurrence" | "validationSurvival">,
): number {
  return (
    0.4 * quality.clustering +
    0.3 * quality.crossDomainRecurrence +
    0.3 * quality.validationSurvival
  );
}

export function computePLAQualityMetrics(
  events: JPSSContributionEvent[],
  ledger: Record<string, LedgerEntry>,
): Pick<PLAMetrics, "clustering" | "crossDomainRecurrence" | "validationSurvival"> {
  const plaEvents = events.filter((e) => e.origin === "PLA");

  if (plaEvents.length === 0) {
    return { clustering: 0, crossDomainRecurrence: 0, validationSurvival: 0 };
  }

  const layerCounts = new Map<string, number>();
  for (const e of plaEvents) {
    layerCounts.set(e.targetsLayer, (layerCounts.get(e.targetsLayer) ?? 0) + 1);
  }
  const maxLayerCount = Math.max(...layerCounts.values());
  const clustering = maxLayerCount / plaEvents.length;

  const distinctLayers = layerCounts.size;
  const crossDomainRecurrence = distinctLayers / plaEvents.length;

  const plaChangeIds = plaEvents.flatMap((e) => e.buildsOn);
  const relevantLedger = plaChangeIds
    .map((id) => ledger[id])
    .filter((entry): entry is LedgerEntry => entry !== undefined);

  const survived = relevantLedger.filter(
    (l) => l.validationResult === "PASSED" && l.finalStatus === "VALIDATED",
  ).length;

  const validationSurvival =
    relevantLedger.length === 0 ? 0 : survived / relevantLedger.length;

  return { clustering, crossDomainRecurrence, validationSurvival };
}

export function computeContinuityMetrics(
  events: JPSSContributionEvent[],
  drift: DriftSignals | null,
  origins?: Record<string, AccumulationOrigin>,
  stewardQualified = false,
  ledger: Record<string, LedgerEntry> = {},
): ContinuityMetrics {
  const eventOrigins = origins ?? classifyEvents(events);
  const accumulationCount = events.filter((e) => e.accumulationType !== "NONE").length;
  const actors = new Set(
    events.filter((e) => e.accumulationType !== "NONE").map((e) => e.actor),
  );

  const plaQuality = computePLAQualityMetrics(events, ledger);
  const pla: PLAMetrics = {
    ...computePLAAccumulationMetrics(events, eventOrigins),
    ...plaQuality,
    instrumentality: computeInstrumentalityIndex(plaQuality),
  };
  const la = computeLAMetrics(events, eventOrigins);
  const sa = computeSAMetrics(events, eventOrigins);
  const reconstructability = computeReconstructability(events);
  const invariants = evaluateInvariantHealth(
    events,
    eventOrigins,
    reconstructability,
    pla.plaToLaIntegrationRate,
  );

  const plt1 = evaluatePLT1(events, eventOrigins);
  const mat3 = evaluateMAT3LA(events, eventOrigins);
  const thresholds = evaluateThresholds(events, eventOrigins, stewardQualified);
  const epistemic = computeEpistemicMetrics(events);

  return {
    accumulationCount,
    distinctActors: actors.size,
    mat3,
    plt1,
    thresholds,
    accumulation: computeAccumulationScore(events, eventOrigins),
    reconstructability,
    drift,
    pla,
    la,
    sa,
    coupling: computeCouplingStrength(events, eventOrigins),
    gravity: computeGravityField(events, eventOrigins),
    invariants,
    interpretation: interpretContinuity(
      pla.plaCount,
      la.laCount,
      pla.plaToLaIntegrationRate,
    ),
    epistemic,
  };
}

export function computeFullContinuity(
  events: JPSSContributionEvent[],
  drift: DriftSignals | null,
  ledger: Record<string, LedgerEntry> = {},
): {
  continuity: ContinuityMetrics;
  eventOrigins: Record<string, AccumulationOrigin>;
  stewardCandidates: ReturnType<typeof evaluateStewardCandidates>;
} {
  const eventOrigins = classifyEvents(events);
  const stewardCandidates = evaluateStewardCandidates(events, eventOrigins);
  const stewardQualified = hasStewardEmergence(stewardCandidates);
  let continuity = computeContinuityMetrics(
    events,
    drift,
    eventOrigins,
    stewardQualified,
    ledger,
  );
  continuity = {
    ...continuity,
    thresholds: evaluateThresholds(events, eventOrigins, stewardQualified),
  };
  return { continuity, eventOrigins, stewardCandidates };
}
