import type { Id, ISOTime } from "../css2/types";

export interface Observation {
  id: Id;
  observerId: Id;
  timestamp: ISOTime;
  domain: string;
  description: string;
  context?: unknown;
  tags?: string[];
}
