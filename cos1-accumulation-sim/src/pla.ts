import {
  AccumulationOrigin,
  ContinuityGravity,
  JPSSContributionEvent,
  PhenomenonLineageCoupling,
  PLACriteria,
  PLAMetrics,
  StewardCandidate,
} from "./domain.js";
import { computePlaToLaIntegrationRate } from "./ce2.js";

const JPSS_LAYERS = new Set(["Continuity", "Transferability", "Governance", "Meta"]);

const STRUCTURAL_TYPES = new Set(["A2", "A3", "A4"]);

export function isPhenomenonAnchored(ev: JPSSContributionEvent): boolean {
  return Boolean(ev.phenomenonAnchor && ev.phenomenonAnchor.trim().length > 0);
}

export function isLineageCompatible(ev: JPSSContributionEvent): boolean {
  if (ev.lineageCompatible === false) return false;
  return JPSS_LAYERS.has(ev.targetsLayer);
}

export function hasExplanatoryGain(ev: JPSSContributionEvent): boolean {
  return ev.accumulationType !== "NONE";
}

export function showsGovernanceBehavior(ev: JPSSContributionEvent): boolean {
  if (ev.governanceBehavior) return true;
  if (ev.targetsLayer === "Governance") return true;
  return ev.accumulationType === "A4" && ev.fromExposure;
}

export function evaluatePLACriteria(ev: JPSSContributionEvent): PLACriteria {
  return {
    noFrameworkExposure: !ev.fromExposure,
    phenomenonAnchored: isPhenomenonAnchored(ev),
    lineageCompatible: isLineageCompatible(ev),
    explanatoryGain: hasExplanatoryGain(ev),
  };
}

export function isPLAEvent(ev: JPSSContributionEvent): boolean {
  const c = evaluatePLACriteria(ev);
  return (
    c.noFrameworkExposure &&
    c.phenomenonAnchored &&
    c.lineageCompatible &&
    c.explanatoryGain
  );
}

import { classifyOrigin } from "./originClassifier.js";

export function classifyAccumulationOrigin(ev: JPSSContributionEvent): AccumulationOrigin | null {
  if (ev.accumulationType === "NONE") return null;
  return ev.origin ?? classifyOrigin(ev);
}

export function classifyEvents(
  events: JPSSContributionEvent[],
): Record<string, AccumulationOrigin> {
  const origins: Record<string, AccumulationOrigin> = {};
  for (const ev of events) {
    const origin = classifyAccumulationOrigin(ev);
    if (origin) origins[ev.id] = origin;
  }
  return origins;
}

export function computePLAMetrics(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
): Pick<
  PLAMetrics,
  "plaCount" | "plaActors" | "plaDepth" | "plaToLaIntegrationRate" | "plaToLaRatio"
> {
  const plaEvents = events.filter((e) => origins[e.id] === "PLA");
  const laEvents = events.filter((e) => origins[e.id] === "LA");

  const plaCount = plaEvents.length;
  const plaActors = new Set(plaEvents.map((e) => e.actor)).size;
  const structuralPla = plaEvents.filter((e) =>
    e.accumulationType === "A2" || e.accumulationType === "A3",
  );

  const plaDepth = plaCount === 0 ? 0 : structuralPla.length / plaCount;
  const plaToLaIntegrationRate = computePlaToLaIntegrationRate(events, origins);
  const plaToLaRatio =
    laEvents.length === 0 ? (plaCount > 0 ? Infinity : 0) : plaCount / laEvents.length;

  return {
    plaCount,
    plaActors,
    plaDepth,
    plaToLaIntegrationRate,
    plaToLaRatio,
  };
}

export function computeCouplingStrength(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
): PhenomenonLineageCoupling {
  const plaEvents = events.filter((e) => origins[e.id] === "PLA");
  const plaTotal = plaEvents.length;
  const plaCompatible = plaEvents.filter(isLineageCompatible).length;

  return {
    plaCompatible,
    plaTotal,
    couplingStrength: plaTotal === 0 ? 0 : plaCompatible / plaTotal,
  };
}

/** G_P = PLA density; G_L = propagation + LA density (CSS-2) */
export function computeGravityField(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
  totalObservers?: number,
): ContinuityGravity {
  const observers = totalObservers ?? new Set(events.map((e) => e.actor)).size;
  const safeObservers = Math.max(observers, 1);

  const plaEvents = events.filter((e) => origins[e.id] === "PLA").length;
  const lineageEvents = events.filter(
    (e) => origins[e.id] === "LA" || origins[e.id] === "SA",
  ).length;

  return {
    phenomenonGravity: plaEvents / safeObservers,
    lineageGravity: lineageEvents / safeObservers,
    totalObservers: safeObservers,
  };
}

function personalK4Satisfied(actorEvents: JPSSContributionEvent[]): boolean {
  const exposureEvents = actorEvents.filter((e) => e.fromExposure);
  const hasStructural = actorEvents.some((e) => STRUCTURAL_TYPES.has(e.accumulationType));
  return exposureEvents.length >= 1 && hasStructural;
}

export function evaluateStewardCandidate(
  actor: string,
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
): StewardCandidate {
  const actorEvents = events.filter((e) => e.actor === actor);
  const plaCapable = actorEvents.some((e) => origins[e.id] === "PLA");
  const laCapable = actorEvents.some(
    (e) => origins[e.id] === "LA" || e.fromExposure,
  );
  const saCapable =
    actorEvents.some((e) => origins[e.id] === "SA") ||
    actorEvents.some(showsGovernanceBehavior);
  const hasPlaOrLa = plaCapable || actorEvents.some((e) => origins[e.id] === "LA");
  const k4Satisfied = personalK4Satisfied(actorEvents);

  const qualified = hasPlaOrLa && k4Satisfied && saCapable;

  return {
    actor,
    qualified,
    plaCapable,
    laCapable,
    saCapable,
    k4Satisfied,
    hasPlaOrLa,
  };
}

export function evaluateStewardCandidates(
  events: JPSSContributionEvent[],
  origins: Record<string, AccumulationOrigin>,
): StewardCandidate[] {
  const actors = new Set(events.map((e) => e.actor));
  return [...actors].map((actor) => evaluateStewardCandidate(actor, events, origins));
}

export function hasStewardEmergence(candidates: StewardCandidate[]): boolean {
  return candidates.some((c) => c.qualified);
}
