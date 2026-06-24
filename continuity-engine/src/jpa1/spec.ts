/** JPA-1 — Judgment Primacy Amendment (constitutional invariant). */

export const JPA1_REFERENCE = "Judgment Primacy Amendment (JPA-1)";
export const JPA1_STATUS = "draft" as const;

export type JudgmentCapabilityDimension =
  | "perception"
  | "interpretation"
  | "valuation"
  | "deliberation"
  | "commitment"
  | "reflection";

export const JPA1_PRINCIPLES = {
  JPA_1_1:
    "Continuity is the preserved capacity of a system to exercise sound, reality-responsive judgment across lineage.",
  JPA_1_2:
    "Reality-responsive observation is necessary but not sufficient for sound judgment.",
  JPA_1_3: "Thresholds and Δ-Thresholds are expressions of judgment, not merely rules.",
  JPA_1_4: "Stewardship is governance of judgment capability across generations.",
  JPA_1_5:
    "The ultimate continuity failure is loss or corruption of judgment capability, even if observers and rules remain intact.",
  JPA_1_8:
    "The ultimate continuity failure is judgment failure — loss or corruption of judgment capability even when observers and rules remain intact.",
} as const;

/** JPA-1.5 / JPA-1.8 — canonical failure statement for compliance checks. */
export const JPA1_8_JUDGMENT_FAILURE = JPA1_PRINCIPLES.JPA_1_8;

export const JPA1_CONTINUITY_DEFINITION = JPA1_PRINCIPLES.JPA_1_1;

export const JPA1_JUDGMENT_PIPELINE = [
  "observation",
  "interpretation",
  "valuation",
  "threshold",
  "delta_threshold",
  "stewardship",
] as const;

/** OPA-1 is necessary; JPA-1 strictly contains it. */
export const OPA1_CONTAINMENT =
  "OPA-1 protects reality-responsive observation; JPA-1 protects sound judgment. CSS-2 requires both; JPA-1 is the deeper invariant.";

/** System mandates under JPA-1 reframing. */
export const JPA1_SYSTEM_MANDATES = {
  JPSS2:
    "Judgment-preservation system for developing and transmitting observational and judgment capabilities across individuals and generations.",
  CSS2:
    "Judgment-preserving runtime for threshold emergence and recalibration; thresholds and Δ-Thresholds are judgment artifacts.",
  CRK1:
    "Constitutional runtime that protects the conditions for legitimate judgment; non-derogable invariants constrain judgment failure modes.",
  RACOS1:
    "Evidence and trace system preserving information required for judgment correction; links observation through recalibration.",
} as const;

export const OPA1_RELATIONSHIP = OPA1_CONTAINMENT;

export const JPA1_OPA1_SUMMARY = {
  opa1: "Necessary for continuity — protects observation conditions.",
  jpa1: "Defines continuity — protects judgment capability.",
} as const;
