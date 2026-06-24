import type { Id, ISOTime } from "../css2/types";
import type { Observation } from "./observation";

export interface Case {
  id: Id;
  createdAt: ISOTime;
  createdBy: Id;
  observations: Observation[];
  hypothesis?: string;
  domain: string;
  status: "open" | "closed" | "escalated";
  tags?: string[];
}
