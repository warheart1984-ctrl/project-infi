import type { ThresholdDelta } from "../css2/types";

export interface TeamReview {
  team: "red" | "blue" | "black" | "white" | "gold";
  passed: boolean;
  notes: string;
}

export interface AdversarialReviewResult {
  passed: boolean;
  reviews: TeamReview[];
  maxAttackScore: number;
  notes: string[];
}

export function runAdversarialReview(
  delta: ThresholdDelta,
  evidence: unknown[],
): AdversarialReviewResult {
  const reviews: TeamReview[] = [];
  const notes: string[] = [];
  let maxAttackScore = 0;

  const largeSwing =
    typeof delta.before.value === "number" &&
    typeof delta.after.value === "number" &&
    Math.abs((delta.after.value as number) - (delta.before.value as number)) >
      Math.abs(delta.before.value as number) * 0.5;

  if (largeSwing) {
    maxAttackScore += 4;
    notes.push("Black: large threshold swing — edge-case risk");
    reviews.push({ team: "black", passed: false, notes: "Large swing detected" });
  } else {
    reviews.push({ team: "black", passed: true, notes: "Edge cases acceptable" });
  }

  if (delta.rationale.toLowerCase().includes("identity")) {
    maxAttackScore += 5;
    notes.push("Red: proposal may affect identity coherence");
    reviews.push({ team: "red", passed: false, notes: "Identity risk" });
  } else {
    reviews.push({ team: "red", passed: true, notes: "No identity attack surface" });
  }

  reviews.push({
    team: "blue",
    passed: true,
    notes: `Defended delta on ${delta.thresholdId}`,
  });

  reviews.push({
    team: "white",
    passed: evidence.length > 0 || Boolean(delta.rationale),
    notes: evidence.length > 0 ? "Evidence documented" : "Missing evidence",
  });

  reviews.push({
    team: "gold",
    passed: maxAttackScore < 7,
    notes: `Attack score ${maxAttackScore}`,
  });

  const passed =
    reviews.every((r) => r.passed) ||
    (maxAttackScore < 5 && evidence.length > 0);

  return { passed, reviews, maxAttackScore, notes };
}
