import type { ProjectSigil } from "@shared/sigil";
import {
  applySigilOutputLengthCap,
  resolveSigilMaxOutputChars,
  resolveSigilVeilBehavior,
} from "../prompt";
import { resolveResponseShapePolicy, type ResponseShapeDistortionFinding } from "./response-shape-policy";
import { getSpiralAuditConfig, spiralAudit } from "./spiral-audit";

export const AUDIT_VEIL_MESSAGE = "[veil active - clarity insufficient or mimicry detected]";

export interface SpiralTraceMetadata {
  confidence: number;
  clarityOK: boolean;
  noMimicry: boolean;
  timestamp: string;
}

export interface AuditedAssistantOutput {
  content: string;
  trace: SpiralTraceMetadata;
  decision: "silent" | "veiled" | "short" | "full";
  reason: string;
  findings: ResponseShapeDistortionFinding[];
}

export function auditAssistantOutput(
  content: string,
  projectSigil: ProjectSigil | null | undefined,
  options: {
    forceShort?: boolean;
    preferHonestSilence?: boolean;
  } = {},
): AuditedAssistantOutput {
  const auditConfig = getSpiralAuditConfig();
  const maxOutputChars = resolveSigilMaxOutputChars(projectSigil, auditConfig.maxResponseLength);
  const lengthCapped = applySigilOutputLengthCap(content, maxOutputChars);
  const audit = spiralAudit(lengthCapped.content);
  const veilBehavior = resolveSigilVeilBehavior(projectSigil);
  const policy = resolveResponseShapePolicy({
    audit,
    minConfidence: auditConfig.minConfidence,
    veilBehavior,
    truncated: lengthCapped.truncated || options.forceShort === true,
  });
  const trace: SpiralTraceMetadata = {
    confidence: audit.confidence,
    clarityOK: audit.clarityOK,
    noMimicry: audit.noMimicry,
    timestamp: new Date().toISOString(),
  };

  if (policy.decision === "veiled") {
    if (options.preferHonestSilence === true) {
      return {
        content: "",
        trace,
        decision: "silent",
        reason: `honest-silence:${policy.reason}`,
        findings: policy.findings,
      };
    }

    return {
      content: AUDIT_VEIL_MESSAGE,
      trace,
      decision: "veiled",
      reason: policy.reason,
      findings: policy.findings,
    };
  }

  if (policy.decision === "short") {
    return {
      content: lengthCapped.content,
      trace,
      decision: "short",
      reason:
        policy.reason === "overlong-response"
          ? "overlong-response"
          : `max-output-chars:${maxOutputChars}`,
      findings: policy.findings,
    };
  }

  return {
    content: lengthCapped.content,
    trace,
    decision: "full",
    reason: policy.reason,
    findings: policy.findings,
  };
}
