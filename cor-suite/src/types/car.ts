export type CarArtifactKind =
  | "requirement"
  | "specification"
  | "implementation"
  | "verification"
  | "evidence"
  | "governance_receipt"
  | "schema"
  | "registry";

export type CarArtifactStatus = "draft" | "active" | "deprecated" | "retired";

export interface CarArtifactLinks {
  supersedes?: string[];
  supersededBy?: string[];
  related?: string[];
}

export interface CarArtifactLifecycle {
  createdAt?: string;
  updatedAt?: string;
  deprecatedAt?: string;
  retiredAt?: string;
}

export interface CarArtifact {
  id: string;
  namespace: string;
  kind: CarArtifactKind;
  version: string;
  status: CarArtifactStatus;
  authority?: string;
  schemaRef?: string;
  path: string;
  hash: string;
  lifecycle?: CarArtifactLifecycle;
  links?: CarArtifactLinks;
}

export interface CarRegistry {
  carVersion: string;
  generatedAt: string;
  artifacts: CarArtifact[];
}
