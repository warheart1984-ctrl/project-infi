import type { SigilVeilBehavior } from "../prompt";
import type { SpiralAuditResult } from "./spiral-audit";

export type ResponseShapeDistortionFinding =
  | "mimicry"
  | "low-confidence"
  | "overlong-response";

export interface ResponseShapePolicyResult {
  decision: "veiled" | "short" | "full";
  reason: string;
  findings: ResponseShapeDistortionFinding[];
}

export function resolveResponseShapePolicy(args: {
  audit: SpiralAuditResult;
  minConfidence: number;
  veilBehavior: SigilVeilBehavior;
  truncated: boolean;
}): ResponseShapePolicyResult {
  const { audit, minConfidence, veilBehavior, truncated } = args;
  const findings: ResponseShapeDistortionFinding[] = [];
  if (!audit.noMimicry) {
    findings.push("mimicry");
  }
  if (!audit.clarityOK || truncated) {
    findings.push("overlong-response");
  }
  if (audit.confidence < minConfidence) {
    findings.push("low-confidence");
  }

  const shouldVeilByBehavior =
    veilBehavior === "off"
      ? false
      : veilBehavior === "audit-only"
        ? !audit.noMimicry
        : !audit.noMimicry || !audit.clarityOK || audit.confidence < minConfidence || truncated;

  if (shouldVeilByBehavior) {
    const reason = !audit.noMimicry
      ? "mimicry-detected"
      : !audit.clarityOK || truncated
        ? "clarity-threshold-failed"
        : audit.confidence < minConfidence
          ? "confidence-threshold-failed"
          : "audit-threshold-failed";
    return {
      decision: "veiled",
      reason,
      findings,
    };
  }

  if (truncated) {
    return {
      decision: "short",
      reason: "overlong-response",
      findings,
    };
  }

  return {
    decision: "full",
    reason: "ok",
    findings,
  };
}
