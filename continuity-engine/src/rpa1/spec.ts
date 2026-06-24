/** RPA-1 — Reality Primacy Amendment (root constitutional invariant). */

export const RPA1_REFERENCE = "Reality Primacy Amendment (RPA-1)";
export const RPA1_STATUS = "draft" as const;

export const RPA1_PRINCIPLES = {
  RPA_1_1:
    "Reality is the final arbiter of judgment. No doctrine, hierarchy, incentive structure, or internal metric may claim higher authority than reality as expressed through evidence.",
  RPA_1_2:
    "Evidence is the constitutionally protected channel through which reality constrains judgment. Any obstruction, fabrication, or suppression of evidence is a constitutional violation.",
  RPA_1_3:
    "Judgment is legitimate only when it remains answerable to evidence. A judgment act that cannot be corrected by evidence is constitutionally illegitimate, regardless of procedure.",
  RPA_1_4:
    "Stewardship is the preservation of reality's authority over judgment across lineage. Future stewards must inherit not conclusions, but the structural ability for reality to correct their conclusions.",
  RPA_1_5:
    "Continuity is the preserved relationship in which reality generates evidence, evidence constrains judgment, judgment produces action, outcomes generate new evidence, and stewards maintain this loop across generations.",
} as const;

export const RPA1_CONTINUITY_DEFINITION = RPA1_PRINCIPLES.RPA_1_5;

export const RPA1_CONTINUITY_FAILURE =
  "Continuity fails when reality loses the ability to correct judgment, even if cycles continue to run.";

/** RPA-1 sits above OPA-1, JPA-1, CRK-1, CSS-2, and RA-COS-1. */
export const RPA1_HIERARCHY = [
  "RPA-1",
  "OPA-1",
  "JPA-1",
  "CRK-1",
  "CSS-2",
  "RA-COS-1",
] as const;

export const RPA1_TO_SYSTEM = {
  RPA1: "Reality Veto — evidence can overrule judgment",
  OPA1: "Evidence integrity — observation tied to reality",
  RACOS1: "Evidence preservation — veto can be proven",
  JPA1: "Judgment capability — judgment can update",
  CRK1J: "Legitimacy — ignoring veto is illegitimate",
  STEWARDSHIP: "Lineage — future stewards inherit veto mechanism",
} as const;

export const RPA1_THOUSAND_YEAR_MOVE =
  "Do not try to predict the future. Encode a structure where reality always wins.";
