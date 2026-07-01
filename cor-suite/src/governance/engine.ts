import { COR_SUITE_PATHS } from "../paths.js";
import type { CorStateVector } from "../types/cor.js";
import type { ProofAnalysisResult } from "../types/analysis.js";
import type { GovernanceDecision, GovernanceReceipt } from "../types/governance.js";
import type { RepoHygieneStatus } from "../types/hygiene.js";
import { CONSTITUTIONAL_INVARIANTS } from "./invariants.js";
import { signReceiptPayload } from "./receipts.js";
import { writeJsonOutput } from "../lib/io.js";

export function applyInvariants(
  cor: CorStateVector,
  analysis: ProofAnalysisResult,
  hygiene?: RepoHygieneStatus,
): GovernanceDecision {
  const criticalClaims = analysis.claims.filter(
    (c) => c.severity === "critical" || c.severity === "error",
  );
  const structuralCritical =
    cor.structuralIntegrity.missingArtifacts.length > 20 ||
    cor.structuralIntegrity.brokenLineage.some((b) => b.issueType === "critical");

  if (hygiene && !hygiene.directoryHygieneOk) return "reject";
  if (criticalClaims.some((c) => c.severity === "critical")) return "freeze";
  if (structuralCritical) return "require_fixes";
  if (criticalClaims.length > 0) return "require_fixes";
  if (cor.structuralIntegrity.brokenLineage.length > 0) return "escalate";
  return "approve";
}

export function runGovernance(
  cor: CorStateVector,
  analysis: ProofAnalysisResult,
  options?: { steward?: string; scope?: string[]; hygiene?: RepoHygieneStatus },
): GovernanceReceipt {
  const decision = applyInvariants(cor, analysis, options?.hygiene);
  const rationaleParts: string[] = [];

  if (options?.hygiene && !options.hygiene.directoryHygieneOk) {
    rationaleParts.push("Repo hygiene failed");
  }
  const critical = analysis.claims.filter((c) => c.severity === "critical" || c.severity === "error");
  if (critical.length > 0) {
    rationaleParts.push(`${critical.length} critical/error proof claims`);
  }
  if (cor.structuralIntegrity.missingArtifacts.length > 0) {
    rationaleParts.push(`${cor.structuralIntegrity.missingArtifacts.length} missing artifact links`);
  }
  if (rationaleParts.length === 0) rationaleParts.push("No blocking invariants detected");

  const timestamp = new Date().toISOString();
  const steward = options?.steward ?? "steward:cor-suite";
  const receiptBase: Omit<GovernanceReceipt, "signature"> = {
    decisionId: `decision-${timestamp.replace(/[:.]/g, "-")}`,
    corStateRef: cor.generatedAt,
    analysisRef: analysis.analysisId,
    decision,
    scope: options?.scope ?? ["project-infi:main"],
    rationale: rationaleParts.join("; "),
    evidenceRefs: [
      COR_SUITE_PATHS.outputs.corState,
      COR_SUITE_PATHS.outputs.proofAnalysis,
    ],
    invariantsEnforced: CONSTITUTIONAL_INVARIANTS.map((i) => i.id),
    steward,
    timestamp,
  };

  return { ...receiptBase, signature: signReceiptPayload(receiptBase) };
}

export function emitGovernanceReceipt(
  cor: CorStateVector,
  analysis: ProofAnalysisResult,
  options?: { steward?: string; scope?: string[]; hygiene?: RepoHygieneStatus },
): string {
  const receipt = runGovernance(cor, analysis, options);
  return writeJsonOutput(COR_SUITE_PATHS.outputs.governanceReceipt, receipt);
}
