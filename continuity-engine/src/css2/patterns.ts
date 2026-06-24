import type { Id, ISOTime, ObservationPattern } from "./types";

export function createObservationPattern(input: {
  id: Id;
  domain: string;
  description: string;
  evidence?: Id[];
  proposedBy: Id;
  tags?: string[];
}): ObservationPattern {
  return {
    id: input.id,
    domain: input.domain,
    description: input.description,
    evidence: input.evidence ?? [],
    proposedBy: input.proposedBy,
    createdAt: new Date().toISOString(),
    status: "open",
    tags: input.tags,
  };
}

export function formalizePattern(pattern: ObservationPattern): ObservationPattern {
  return { ...pattern, status: "formalized" };
}

export function rejectPattern(pattern: ObservationPattern): ObservationPattern {
  return { ...pattern, status: "rejected" };
}
