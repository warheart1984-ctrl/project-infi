export interface ProofAnalysisResult {
  analysisId: string;
  corStateRef: string;
  generatedAt: string;
  claims: Array<{
    claimId: string;
    type: string;
    summary: string;
    severity: "info" | "warning" | "error" | "critical";
    derivation: string[];
    relatedRequirements?: string[];
  }>;
  dependencyMaps?: Array<{ rootRequirementId: string; dependencies: string[] }>;
  regressions?: Array<{
    regressionId: string;
    kind: "implementation" | "verification" | "evidence";
    requirementId: string;
    description: string;
  }>;
}
