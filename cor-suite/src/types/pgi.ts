export type PgiNodeKind =
  | "requirement"
  | "specification"
  | "implementation"
  | "verification"
  | "evidence"
  | "governance_receipt";

export type PgiEdgeRelation =
  | "implements"
  | "verifies"
  | "evidences"
  | "supersedes"
  | "related";

export interface PgiNode {
  id: string;
  kind: PgiNodeKind;
  path: string;
}

export interface PgiEdge {
  from: string;
  to: string;
  relation: PgiEdgeRelation;
}

export interface Pgi {
  pgiVersion: string;
  generatedAt: string;
  nodes: PgiNode[];
  edges: PgiEdge[];
}
