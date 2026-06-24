import type { Id, ISOTime } from "../css2/types";
import type { Evidence } from "./evidence";

export interface Audit {
  id: Id;
  subjectId: Id;
  subjectType: string;
  createdAt: ISOTime;
  createdBy: Id;
  evidence: Evidence[];
  conclusion: "valid" | "invalid" | "uncertain";
  rationale: string;
  recommendations?: string[];
}
