import type { Comparator, Id, ProtoThreshold } from "./types";

export function createProtoThreshold(input: {
  id: Id;
  patternId: Id;
  domain: string;
  metric: string;
  comparator: Comparator;
  value: unknown;
  intent: string;
  proposedBy: Id;
  unit?: string;
  notes?: string;
}): ProtoThreshold {
  return {
    id: input.id,
    patternId: input.patternId,
    domain: input.domain,
    metric: input.metric,
    comparator: input.comparator,
    value: input.value,
    unit: input.unit,
    intent: input.intent,
    proposedBy: input.proposedBy,
    createdAt: new Date().toISOString(),
    status: "draft",
    notes: input.notes,
  };
}

export function markProtoThresholdAdopted(proto: ProtoThreshold): ProtoThreshold {
  return { ...proto, status: "adopted" };
}

export function rejectProtoThreshold(proto: ProtoThreshold): ProtoThreshold {
  return { ...proto, status: "rejected" };
}
