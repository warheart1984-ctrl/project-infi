import type {
  JPSSContributionEvent,
  JPSSContributionEventInput,
  EpistemicMode,
} from "./domain.js";
import { withOrigin } from "./originClassifier.js";

export function classifyMode(
  ev: Pick<JPSSContributionEvent, "accumulationType" | "fromExposure"> & {
    mode?: EpistemicMode;
  },
): EpistemicMode {
  if (ev.mode) return ev.mode;
  if (ev.accumulationType === "NONE" && !ev.fromExposure) return "OBSERVATION";
  return "INTERPRETATION";
}

export function withMode(
  ev: Omit<JPSSContributionEvent, "mode"> & { mode?: EpistemicMode },
): JPSSContributionEvent {
  return {
    ...ev,
    mode: ev.mode ?? classifyMode(ev),
  };
}

/** Apply origin + epistemic mode tags at ingestion */
export function withEventTags(ev: JPSSContributionEventInput): JPSSContributionEvent {
  const withOrig = withOrigin(ev);
  return withMode({ ...withOrig, mode: ev.mode });
}
