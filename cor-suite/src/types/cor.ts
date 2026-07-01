export type MaturityLevel = "normative" | "implemented" | "verified" | "reproduced";

export type ReproductionStatus = "not_attempted" | "in_progress" | "failed" | "succeeded";

export interface ArtifactRef {
  path: string;
  type: string;
  hash: string;
}

export interface CorRequirement {
  id: string;
  authority: string;
  specArtifacts: ArtifactRef[];
  implArtifacts: ArtifactRef[];
  verificationArtifacts: ArtifactRef[];
  evidence: Array<{ id: string; type: string; artifact: ArtifactRef }>;
  provenance: Array<{
    eventId: string;
    actor: string;
    timestamp: string;
    action: string;
    details?: string;
  }>;
  reproductionStatus: ReproductionStatus;
  maturity: MaturityLevel;
}

export interface CorStateVector {
  corVersion: string;
  generatedAt: string;
  commit?: string;
  requirements: CorRequirement[];
  artifactIndex?: {
    specifications: ArtifactRef[];
    implementations: ArtifactRef[];
    verifications: ArtifactRef[];
    evidence: ArtifactRef[];
  };
  structuralIntegrity: {
    orphans: {
      requirements: string[];
      implementations: string[];
      verifications: string[];
    };
    missingArtifacts: Array<{
      expectedForRequirement: string;
      kind: "spec" | "impl" | "verification" | "evidence";
    }>;
    brokenLineage: Array<{ fromId: string; toId: string; issueType: string; details?: string }>;
    unresolvedAssumptions: string[];
  };
}
