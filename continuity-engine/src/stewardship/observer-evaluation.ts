import type { ObserverProfile } from "../css2/types";

export interface ObserverEffectiveness {
  score: number;
  notes: string[];
}

export function evaluateObserverEffectiveness(
  observer: ObserverProfile,
): ObserverEffectiveness {
  const caps = observer.capabilities;
  const avg =
    (caps.perception +
      caps.interpretation +
      caps.hypothesis +
      caps.judgment +
      caps.stewardship) /
    5;

  const notes: string[] = [];
  if (caps.perception < 0.4) notes.push("Weak perception");
  if (caps.stewardship < 0.4) notes.push("Weak self-correction");

  return { score: avg, notes };
}
