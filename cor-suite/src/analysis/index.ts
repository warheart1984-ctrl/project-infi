import { COR_SUITE_PATHS } from "../paths.js";
import type { CorStateVector } from "../types/cor.js";
import type { ProofAnalysisResult } from "../types/analysis.js";
import { readJsonInput, writeJsonOutput } from "../lib/io.js";

export function runProofAnalysis(cor?: CorStateVector): ProofAnalysisResult {
  const corState = cor ?? readJsonInput<CorStateVector>(COR_SUITE_PATHS.outputs.corState);
  const analysisId = `analysis-${corState.generatedAt.replace(/[:.]/g, "-")}`;
  const claims: ProofAnalysisResult["claims"] = [];

  const orphanImplCount = corState.structuralIntegrity.orphans.implementations.length;
  const orphanVerCount = corState.structuralIntegrity.orphans.verifications.length;
  const missingCount = corState.structuralIntegrity.missingArtifacts.length;

  if (orphanImplCount > 0) {
    claims.push({
      claimId: "PA-ORPHAN-IMPL",
      type: "structural.orphan_implementation",
      summary: `${orphanImplCount} implementation artifacts outside requirement namespaces`,
      severity: orphanImplCount > 50 ? "warning" : "info",
      derivation: ["cor.structuralIntegrity.orphans.implementations"],
    });
  }

  if (orphanVerCount > 0) {
    claims.push({
      claimId: "PA-ORPHAN-VER",
      type: "structural.orphan_verification",
      summary: `${orphanVerCount} verification artifacts outside requirement namespaces`,
      severity: "info",
      derivation: ["cor.structuralIntegrity.orphans.verifications"],
    });
  }

  for (const missing of corState.structuralIntegrity.missingArtifacts) {
    claims.push({
      claimId: `PA-MISSING-${missing.expectedForRequirement}-${missing.kind}`,
      type: "structural.missing_artifact",
      summary: `Requirement ${missing.expectedForRequirement} missing ${missing.kind}`,
      severity: missing.kind === "verification" ? "error" : "warning",
      derivation: ["cor.structuralIntegrity.missingArtifacts"],
      relatedRequirements: [missing.expectedForRequirement],
    });
  }

  if (missingCount > 10) {
    claims.push({
      claimId: "PA-MISSING-BULK",
      type: "structural.missing_bulk",
      summary: `${missingCount} missing artifact links across requirements`,
      severity: "critical",
      derivation: ["cor.structuralIntegrity.missingArtifacts"],
    });
  }

  const dependencyMaps = corState.requirements.map((r) => ({
    rootRequirementId: r.id,
    dependencies: r.implArtifacts.slice(0, 5).map((a) => a.path),
  }));

  const regressions = claims
    .filter((c) => c.type.startsWith("structural.missing"))
    .map((c, i) => ({
      regressionId: `REG-${i + 1}`,
      kind: "verification" as const,
      requirementId: c.relatedRequirements?.[0] ?? "unknown",
      description: c.summary,
    }));

  const result: ProofAnalysisResult = {
    analysisId,
    corStateRef: corState.generatedAt,
    generatedAt: new Date().toISOString(),
    claims,
    dependencyMaps,
    regressions,
  };

  return result;
}

export function emitProofAnalysis(cor?: CorStateVector): string {
  const result = runProofAnalysis(cor);
  return writeJsonOutput(COR_SUITE_PATHS.outputs.proofAnalysis, result);
}
