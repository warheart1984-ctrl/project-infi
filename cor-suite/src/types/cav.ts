export type CavFindingSeverity = "info" | "warning" | "error" | "critical";

export type CavFindingCategory =
  | "schema"
  | "integrity"
  | "duplicate_id"
  | "lifecycle"
  | "hash_mismatch"
  | "missing_path"
  | "advisory";

export interface CavFinding {
  findingId: string;
  category: CavFindingCategory;
  severity: CavFindingSeverity;
  artifactId?: string;
  path?: string;
  message: string;
  blocking: boolean;
}

export interface CavValidationResult {
  cavVersion: "1.0.0";
  carRef: string;
  generatedAt: string;
  valid: boolean;
  blockingCount: number;
  advisoryCount: number;
  findings: CavFinding[];
}

/** Simplified CAV report shape (stub API). */
export interface CavReportEntry {
  id: string;
  issue: string;
  detail: string;
}

export interface CavReport {
  cavVersion: string;
  generatedAt: string;
  blocking: CavReportEntry[];
  advisory: CavReportEntry[];
}
