import type { Id, ISOTime } from "../css2/types";
import type { Truth } from "./truth";

export interface Memory {
  id: Id;
  truths: Truth[];
  createdAt: ISOTime;
  scope: string;
}

export function truthToMemory(truths: Truth[], scope: string): Memory {
  return {
    id: `memory-${Date.now()}`,
    truths,
    createdAt: new Date().toISOString(),
    scope,
  };
}
