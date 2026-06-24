import type { ObserverProfile } from "../css2/types";

export interface CaptureSignal {
  score: number;
  reasons: string[];
}

export function detectObserverCapture(
  _observer: ObserverProfile,
  incentiveAlignmentScore: number,
  dissentFrequency: number,
): CaptureSignal {
  const reasons: string[] = [];
  let score = 0;

  if (incentiveAlignmentScore > 0.8) {
    score += 0.5;
    reasons.push("High alignment with external incentives");
  }

  if (dissentFrequency < 0.1) {
    score += 0.3;
    reasons.push("Very low dissent frequency");
  }

  return {
    score: Math.min(1, score),
    reasons,
  };
}
