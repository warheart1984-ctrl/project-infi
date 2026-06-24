import type { Id, ISOTime } from "../css2/types";
import type { Audit } from "./audit";

export interface Transfer {
  id: Id;
  fromContext: string;
  toContext: string;
  createdAt: ISOTime;
  createdBy: Id;
  audits: Audit[];
  summary: string;
  medium: "doc" | "training" | "code" | "ritual" | "other";
}
