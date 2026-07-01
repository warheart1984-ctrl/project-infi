export interface CsrReport {
  csrVersion: string;
  generatedAt: string;
  stewardParticipation: {
    registeredReceipts: number;
    uniqueStewards: number;
  };
  governanceActivity: {
    activeRequirements: number;
    governanceArtifacts: number;
  };
  decisionCoverage: {
    requirementsTotal: number;
    requirementsWithGovernanceLink: number;
    coverageRatio: number;
  };
}
