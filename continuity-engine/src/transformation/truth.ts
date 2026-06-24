import type { Id } from "../css2/types";
import type { Evidence } from "../observer-evidence/evidence";
import type { RealitySlice } from "./reality";

export interface Truth {
  id: Id;
  claim: string;
  evidence: Evidence[];
  confidence: number;
}

export function realityToTruth(
  reality: RealitySlice,
  claim: string,
  evidence: Evidence[],
): Truth {
  const strengthAvg =
    evidence.length === 0
      ? 0
      : evidence.reduce((s, e) => s + e.strength, 0) / evidence.length;

  return {
    id: `truth-${Date.now()}`,
    claim,
    evidence,
    confidence: strengthAvg,
  };
}
