/**
 * Interpretive Stewardship — ObservationPattern → ProtoThreshold → Threshold.
 *
 * Operational stewardship governs Δ-Threshold on existing Threshold objects.
 * Interpretive stewardship governs discovery and formalization of new thresholds.
 */

import { createObservationPattern, formalizePattern, rejectPattern } from "../css2/patterns";
import { createProtoThreshold } from "../css2/proto-threshold";
import type {
  ObservationPattern,
  ProtoThreshold,
  Threshold,
  ThresholdCreateInput,
} from "../css2/types";
import type { ThresholdRegistry } from "../registry/threshold-registry";

export interface InterpretiveStore {
  patterns: Map<string, ObservationPattern>;
  protoThresholds: Map<string, ProtoThreshold>;
}

export function createInterpretiveStore(): InterpretiveStore {
  return {
    patterns: new Map(),
    protoThresholds: new Map(),
  };
}

export function recordObservation(
  store: InterpretiveStore,
  input: Omit<ObservationPattern, "createdAt" | "status">,
): ObservationPattern {
  const pattern = createObservationPattern({
    id: input.id,
    domain: input.domain,
    description: input.description,
    evidence: input.evidence,
    proposedBy: input.proposedBy,
    tags: input.tags,
  });
  store.patterns.set(pattern.id, pattern);
  return pattern;
}

export function proposeProtoThreshold(
  store: InterpretiveStore,
  input: Omit<ProtoThreshold, "createdAt" | "status">,
): ProtoThreshold | null {
  const pattern = store.patterns.get(input.patternId);
  if (!pattern || pattern.status !== "open") return null;

  const proto = createProtoThreshold({
    id: input.id,
    patternId: input.patternId,
    domain: input.domain,
    metric: input.metric,
    comparator: input.comparator,
    value: input.value,
    intent: input.intent,
    proposedBy: input.proposedBy,
    unit: input.unit,
    notes: input.notes,
  });
  store.protoThresholds.set(proto.id, proto);
  return proto;
}

export function advanceProtoToTesting(
  store: InterpretiveStore,
  protoId: string,
): ProtoThreshold | null {
  const proto = store.protoThresholds.get(protoId);
  if (!proto || proto.status !== "draft") return null;
  const updated: ProtoThreshold = { ...proto, status: "testing" };
  store.protoThresholds.set(protoId, updated);
  return updated;
}

export interface AdoptProtoResult {
  threshold: Threshold;
  proto: ProtoThreshold;
  pattern: ObservationPattern;
}

/** Promote a tested ProtoThreshold to a governed operational Threshold. */
export async function adoptProtoThreshold(
  store: InterpretiveStore,
  registry: ThresholdRegistry,
  protoId: string,
  thresholdInput: Omit<ThresholdCreateInput, "domain" | "metric" | "intent"> & {
    id: string;
  },
): Promise<AdoptProtoResult | null> {
  const proto = store.protoThresholds.get(protoId);
  if (!proto || proto.status !== "testing") return null;

  const pattern = store.patterns.get(proto.patternId);
  if (!pattern) return null;

  const threshold = await registry.create({
    id: thresholdInput.id,
    name: thresholdInput.name,
    domain: proto.domain,
    metric: proto.metric,
    comparator: proto.comparator,
    value: proto.value,
    unit: thresholdInput.unit ?? proto.unit,
    context: thresholdInput.context,
    intent: proto.intent,
    createdBy: thresholdInput.createdBy,
    lastUpdatedBy: thresholdInput.lastUpdatedBy ?? thresholdInput.createdBy,
  });

  const adoptedProto: ProtoThreshold = { ...proto, status: "adopted" };
  store.protoThresholds.set(protoId, adoptedProto);

  const formalizedPattern = formalizePattern(pattern);
  store.patterns.set(pattern.id, formalizedPattern);

  return {
    threshold,
    proto: adoptedProto,
    pattern: formalizedPattern,
  };
}

export function rejectObservation(
  store: InterpretiveStore,
  patternId: string,
): ObservationPattern | null {
  const pattern = store.patterns.get(patternId);
  if (!pattern) return null;
  const rejected = rejectPattern(pattern);
  store.patterns.set(patternId, rejected);
  return rejected;
}

export function rejectProtoThresholdInStore(
  store: InterpretiveStore,
  protoId: string,
): ProtoThreshold | null {
  const proto = store.protoThresholds.get(protoId);
  if (!proto) return null;
  const rejected: ProtoThreshold = { ...proto, status: "rejected" };
  store.protoThresholds.set(protoId, rejected);
  return rejected;
}
