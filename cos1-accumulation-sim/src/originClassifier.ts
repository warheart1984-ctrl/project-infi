import type { JPSSContributionEvent, AccumulationOrigin, EpistemicMode } from "./domain.js";

export function classifyOrigin(
  ev: Pick<JPSSContributionEvent, "fromExposure" | "accumulationType">,
): AccumulationOrigin {
  if (!ev.fromExposure) return "PLA";
  if (ev.accumulationType === "A1" || ev.accumulationType === "A2") return "LA";
  if (ev.accumulationType === "A3" || ev.accumulationType === "A4") return "SA";
  return "LA";
}

export function withOrigin(
  ev: Omit<JPSSContributionEvent, "origin" | "mode"> & {
    origin?: AccumulationOrigin;
    mode?: EpistemicMode;
  },
): Omit<JPSSContributionEvent, "mode"> & { mode?: EpistemicMode } {
  return {
    ...ev,
    origin: ev.origin ?? classifyOrigin(ev),
  };
}
