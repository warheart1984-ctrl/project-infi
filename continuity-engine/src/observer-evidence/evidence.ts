import type { Id, ISOTime } from "../css2/types";
import type { Case } from "./case";

export type EvidenceDirection = "for" | "against" | "inconclusive";

export interface Evidence {
  id: Id;
  caseId: Id;
  createdAt: ISOTime;
  createdBy: Id;
  claim: string;
  direction: EvidenceDirection;
  strength: number;
  details?: string;
  relatedCases?: Case[];
}
