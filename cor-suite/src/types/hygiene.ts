export interface HygieneIssue {
  issueId: string;
  category: "determinism" | "directory_hygiene" | "canonical_paths" | "reproducibility" | "ci_cd" | "other";
  description: string;
  severity: "info" | "warning" | "error" | "critical";
}

export interface RepoHygieneStatus {
  repoId: string;
  scanTimestamp: string;
  deterministicArtifacts: boolean;
  directoryHygieneOk: boolean;
  canonicalPathsOk: boolean;
  reproducibleBuildsOk: boolean;
  ciCdIntegrated: boolean;
  issues: HygieneIssue[];
}
