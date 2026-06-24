import type { Id } from "../css2/types";
import type { Memory } from "./memory";

export interface Continuity {
  id: Id;
  memory: Memory;
  usageContexts: string[];
  healthScore: number;
}

export function memoryToContinuity(memory: Memory, usageContexts: string[]): Continuity {
  const health = usageContexts.length === 0 ? 0 : Math.min(1, usageContexts.length / 5);
  return {
    id: `continuity-${Date.now()}`,
    memory,
    usageContexts,
    healthScore: health,
  };
}
