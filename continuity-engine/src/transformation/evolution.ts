import type { Id } from "../css2/types";
import type { Continuity } from "./continuity";

export interface Evolution {
  id: Id;
  continuity: Continuity;
  newCapabilities: string[];
  description: string;
}

export function continuityToEvolution(
  continuity: Continuity,
  newCapabilities: string[],
  description: string,
): Evolution {
  return {
    id: `evolution-${Date.now()}`,
    continuity,
    newCapabilities,
    description,
  };
}
