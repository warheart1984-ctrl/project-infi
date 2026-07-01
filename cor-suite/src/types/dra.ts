export interface DraRiskEntry {
  requirementId: string;
  dependencyDepth: number;
  fanIn: number;
  fanOut: number;
  verificationGaps: number;
  deprecatedDependencies: number;
  score: number;
}

export interface DraReport {
  draVersion: string;
  generatedAt: string;
  risk: Record<string, DraRiskEntry>;
}
