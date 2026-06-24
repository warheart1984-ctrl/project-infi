import type { ObserverProfile } from "../css2/types";
import type { CurriculumModule } from "./curriculum";

export function applyCurriculumModule(
  observer: ObserverProfile,
  module: CurriculumModule,
): ObserverProfile {
  if (!module.targetStages.includes(observer.stage)) {
    return observer;
  }
  const caps = { ...observer.capabilities };
  for (const [k, v] of Object.entries(module.effects)) {
    const key = k as keyof typeof caps;
    caps[key] = Math.min(1, caps[key] + (v ?? 0));
  }
  return { ...observer, capabilities: caps };
}
