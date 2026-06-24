import type { Id, ISOTime } from "../css2/types";
import type { Transfer } from "./transfer";

export interface Extension {
  id: Id;
  createdAt: ISOTime;
  createdBy: Id;
  basedOnTransferId: Id;
  description: string;
  changeType: "threshold" | "process" | "architecture" | "culture" | "other";
  diffSummary?: string;
  transfer: Transfer;
}
