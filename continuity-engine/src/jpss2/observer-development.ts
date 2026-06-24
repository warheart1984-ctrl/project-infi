import type { ObserverProfile } from "../css2/types";
import { applyCurriculumModule } from "./apply-curriculum";
import { JPSS2_CURRICULUM } from "./curriculum";
import { advanceObserverStage, runObserverLifecycle } from "../css2/observer-lifecycle";

export function developObserver(
  observer: ObserverProfile,
  moduleIds: string[] = JPSS2_CURRICULUM.map((m) => m.id),
): ObserverProfile {
  let current = observer;
  for (const modId of moduleIds) {
    const mod = JPSS2_CURRICULUM.find((m) => m.id === modId);
    if (mod) {
      current = applyCurriculumModule(current, mod);
    }
  }
  current = runObserverLifecycle(current);
  if (current.capabilities.stewardship >= 0.8 && current.stage === "senior_observer") {
    current = advanceObserverStage(current);
  }
  return current;
}

export { advanceObserverStage, evaluateObserverCapabilities } from "../css2/observer-lifecycle";
