import type { ObserverProfile } from "../css2/types";
import type { JudgmentCapability } from "./capability";

/**
 * Map JPSS-2 observer capabilities to JPA-1 judgment dimensions.
 *
 * hypothesis → deliberation (formulating testable claims)
 * judgment   → commitment (threshold adoption)
 * stewardship → reflection (self-correction)
 * valuation derived from interpretation + hypothesis blend
 */
export function judgmentFromObserver(observer: ObserverProfile): JudgmentCapability {
  const c = observer.capabilities;
  return {
    perception: c.perception,
    interpretation: c.interpretation,
    valuation: (c.interpretation + c.hypothesis) / 2,
    deliberation: c.hypothesis,
    commitment: c.judgment,
    reflection: c.stewardship,
  };
}
