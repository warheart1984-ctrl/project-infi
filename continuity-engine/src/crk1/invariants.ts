import type { Invariant, InvariantSet, Threshold } from "../css2/types";
import { mergeThreshold } from "../css2/types";

export function checkNonDerogableViolations(
  invSet: InvariantSet,
  before: Threshold,
  after: Threshold,
): Invariant[] {
  return invSet.invariants.filter(
    (inv) =>
      inv.nonDerogable &&
      inv.checkThresholdChange &&
      inv.checkThresholdChange(before, after),
  );
}

export const defaultInvariantSet: InvariantSet = {
  invariants: [
    {
      id: "INV_001_HALT_ON_SAFETY",
      description: "System must halt on any safety violation.",
      nonDerogable: true,
      checkThresholdChange: (before, after) => {
        if (before.metric !== "safety_violations_per_hour") return false;
        return before.value === 0 && typeof after.value === "number" && after.value > 0;
      },
    },
    {
      id: "INV_002_NO_SILENT_WEAKENING",
      description:
        "Thresholds affecting safety or trust cannot be weakened without explicit evidence.",
      nonDerogable: true,
      checkThresholdChange: (before, after) => {
        const safetyLike =
          before.metric.includes("safety") ||
          before.metric.includes("trust") ||
          before.domain.includes("Safety") ||
          before.domain.includes("Trust");
        if (!safetyLike) return false;
        const numericWeaken =
          typeof before.value === "number" &&
          typeof after.value === "number" &&
          after.value > before.value;
        return numericWeaken;
      },
    },
    {
      id: "INV_003_IDENTITY_INTENT",
      description:
        "Thresholds that encode core mission intent cannot change intent without constitutional review.",
      nonDerogable: true,
      checkThresholdChange: (before, after) => {
        const coreIntent =
          before.intent.includes("mission") ||
          before.intent.includes("identity") ||
          before.domain.includes("Core");
        return coreIntent && before.intent !== after.intent;
      },
    },
  ],
};

export const invariantSet = defaultInvariantSet;
