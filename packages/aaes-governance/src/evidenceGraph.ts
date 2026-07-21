import type {
  ClaimType,
  ProofLevel,
  ProofSurface,
  ProofSurfaceCommercialReadiness,
  ProofSurfaceOperationalStatus,
  ProofSurfaceValidationIssue,
} from './proofSurface.js';
import { minProofLevelForClaimType, validateProofSurface } from './proofSurface.js';

export type ConstitutionalEvidenceGraphSource = 'release-receipt' | 'local-registry' | 'live-backend';

export type ConstitutionalEvidenceGraphNodeKind =
  | 'root-receipt'
  | 'public-view'
  | 'proof-surface'
  | 'claim'
  | 'evidence';

export type ConstitutionalEvidenceGraphNodeStatus = 'Observed' | 'Hypothesized' | 'Unknown' | 'Verified';

export type ConstitutionalEvidenceGraphEdgeRelation =
  | 'roots'
  | 'publishes'
  | 'contains'
  | 'supports'
  | 'resolves'
  | 'references';

export interface ConstitutionalReleaseReceiptEvidenceSection {
  status: string;
  evidence: string[];
  notes: string[];
}

export interface ConstitutionalReleaseReceipt {
  receiptId: string;
  release?: {
    name: string;
    version: string;
    bundle: string;
    artifactCount: number;
    checksumCount: number;
    signature?: string | null;
  };
  proofSurfaceLevel: ProofLevel;
  buildEvidence: ConstitutionalReleaseReceiptEvidenceSection;
  testEvidence: ConstitutionalReleaseReceiptEvidenceSection;
  lintStatus: ConstitutionalReleaseReceiptEvidenceSection;
  replayStatus: ConstitutionalReleaseReceiptEvidenceSection;
  auditStatus: ConstitutionalReleaseReceiptEvidenceSection;
  verificationDate?: string | null;
  knownLimitations?: string[];
  truthBoundary: string;
  constitutionalMaturity: string;
  commercialReadiness: string;
  generatedAt?: string;
  constitutionalEvidenceGraph?: ConstitutionalEvidenceGraph;
}

export interface ConstitutionalEvidenceGraphView {
  id: string;
  label: string;
  claimIds: string[];
  proofSurfaceIds: string[];
}

export interface ConstitutionalEvidenceGraphNode {
  id: string;
  kind: ConstitutionalEvidenceGraphNodeKind;
  label: string;
  status: ConstitutionalEvidenceGraphNodeStatus;
  proofLevel: ProofLevel;
  source: ConstitutionalEvidenceGraphSource;
  verified: boolean;
  replayable: boolean;
  truthBoundary?: string;
  currentMaturity?: ProofSurfaceOperationalStatus;
  commercialReadiness?: ProofSurfaceCommercialReadiness;
  proofSurfaceId?: string;
  claimId?: string;
  evidenceId?: string;
  claimType?: ClaimType;
}

export interface ConstitutionalEvidenceGraphEdge {
  id: string;
  from: string;
  to: string;
  relation: ConstitutionalEvidenceGraphEdgeRelation;
}

export interface ConstitutionalEvidenceGraphClaimResolution {
  claimId: string;
  claimType: ClaimType;
  proofSurfaceId: string;
  evidenceIds: string[];
  proofLevel: ProofLevel;
  verified: boolean;
  replayable: boolean;
  issues: string[];
}

export interface ConstitutionalEvidenceGraphProofSurface {
  proofSurfaceId: string;
  proofLevel: ProofLevel;
  verificationStatus: string;
  replayStatus: string;
  operationalStatus: ProofSurfaceOperationalStatus;
  truthBoundary: string;
  currentMaturity: ProofSurfaceOperationalStatus;
  commercialReadiness: ProofSurfaceCommercialReadiness;
  nextRequiredEvidence: string[];
}

export interface ConstitutionalEvidenceGraphSummary {
  graphId: string;
  rootReceiptId: string;
  source: ConstitutionalEvidenceGraphSource;
  proofSurfaceCount: number;
  claimCount: number;
  verifiedClaimCount: number;
  replayableClaimCount: number;
  unresolvedClaims: string[];
  viewCount: number;
}

export interface ConstitutionalEvidenceGraph {
  schemaVersion: '1.0';
  graphId: string;
  generatedAt: string;
  source: ConstitutionalEvidenceGraphSource;
  rootReceipt: ConstitutionalReleaseReceipt;
  proofSurfaces: ConstitutionalEvidenceGraphProofSurface[];
  claims: ConstitutionalEvidenceGraphClaimResolution[];
  views: ConstitutionalEvidenceGraphView[];
  nodes: ConstitutionalEvidenceGraphNode[];
  edges: ConstitutionalEvidenceGraphEdge[];
  unresolvedClaims: string[];
  summary: ConstitutionalEvidenceGraphSummary;
}

export interface ConstitutionalEvidenceGraphValidationIssue extends ProofSurfaceValidationIssue {
  scope: 'graph' | 'surface' | 'claim' | 'receipt';
}

export const CONSTITUTIONAL_EVIDENCE_GRAPH_JSON_SCHEMA_VERSION = '1.0';

export const CONSTITUTIONAL_EVIDENCE_GRAPH_JSON_SCHEMA = {
  $schema: 'https://json-schema.org/draft/2020-12/schema',
  title: 'Constitutional Evidence Graph',
  type: 'object',
  required: ['schemaVersion', 'generatedAt', 'source', 'rootReceipt', 'proofSurfaces', 'claims', 'views', 'nodes', 'edges', 'summary'],
  properties: {
    schemaVersion: { const: CONSTITUTIONAL_EVIDENCE_GRAPH_JSON_SCHEMA_VERSION },
    generatedAt: { type: 'string', format: 'date-time' },
    source: { type: 'string' },
    rootReceipt: { type: 'object' },
    proofSurfaces: { type: 'array' },
    claims: { type: 'array' },
    views: { type: 'array' },
    nodes: { type: 'array' },
    edges: { type: 'array' },
    unresolvedClaims: { type: 'array' },
    summary: { type: 'object' },
  },
  additionalProperties: false,
} as const;

const VIEW_DEFINITIONS: ConstitutionalEvidenceGraphView[] = [
  { id: 'view:readme', label: 'README', claimIds: [], proofSurfaceIds: [] },
  { id: 'view:docs-site', label: 'docs-site', claimIds: [], proofSurfaceIds: [] },
  { id: 'view:scorecards', label: 'Scorecards', claimIds: [], proofSurfaceIds: [] },
  { id: 'view:nova-studio', label: 'Nova Studio', claimIds: [], proofSurfaceIds: [] },
  { id: 'view:ops-console', label: 'Ops Console', claimIds: [], proofSurfaceIds: [] },
];

function clone<T>(value: T): T {
  return structuredClone(value);
}

function stripReceiptGraph(receipt: ConstitutionalReleaseReceipt): ConstitutionalReleaseReceipt {
  const { constitutionalEvidenceGraph: _graph, ...rest } = receipt;
  return clone(rest);
}

function proofLevelRank(level: ProofLevel): number {
  return { P0: 0, P1: 1, P2: 2, P3: 3, P4: 4, P5: 5 }[level];
}

function highestProofLevel(levels: ProofLevel[]): ProofLevel {
  return levels.reduce<ProofLevel>((highest, level) => (proofLevelRank(level) > proofLevelRank(highest) ? level : highest), 'P0');
}

function highestMaturity(surfaces: readonly ProofSurface[]): ProofSurfaceOperationalStatus {
  const order: ProofSurfaceOperationalStatus[] = [
    'Scaffold',
    'Prototype',
    'Verified Prototype',
    'Reference Implementation',
    'Production Candidate',
    'Production',
  ];
  return surfaces.reduce<ProofSurfaceOperationalStatus>((highest, surface) => {
    const current = surface.constitutionalProfile.currentMaturity;
    return order.indexOf(current) > order.indexOf(highest) ? current : highest;
  }, 'Scaffold');
}

function buildEvidenceSection(status: string, evidence: string[], notes: string[]): ConstitutionalReleaseReceiptEvidenceSection {
  return {
    status,
    evidence: [...evidence],
    notes: [...notes],
  };
}

function makeSyntheticReceipt(surfaces: readonly ProofSurface[], generatedAt: string): ConstitutionalReleaseReceipt {
  const proofLevel = highestProofLevel(surfaces.map((surface) => surface.proofLevel));
  const maturity = highestMaturity(surfaces);
  const replayableCount = surfaces.filter((surface) => surface.replayStatus !== 'NotAvailable').length;

  return {
    receiptId: 'graph:local-registry',
    proofSurfaceLevel: proofLevel,
    buildEvidence: buildEvidenceSection('Observed', ['local proof-surface registry'], ['Synthetic graph root for local inspection.']),
    testEvidence: buildEvidenceSection('Observed', ['proof-surface validation'], ['Local graph uses the workspace proof-surface registry.']),
    lintStatus: buildEvidenceSection('Unknown', ['workspace lint'], ['Synthetic local graph does not assert lint verification.']),
    replayStatus: buildEvidenceSection('Observed', [`${replayableCount} replayable proof surfaces`], ['Local graph resolution is replayable from source data.']),
    auditStatus: buildEvidenceSection('Observed', ['proof-surface summaries', 'graph resolver'], ['Graph root is derived from live proof-surface evidence.']),
    truthBoundary: 'Synthetic local evidence graph derived from proof surfaces, not the canonical release receipt.',
    constitutionalMaturity: maturity,
    commercialReadiness: 'Prototype',
    knownLimitations: ['Local graph resolution does not replace the canonical release receipt.'],
    generatedAt,
  };
}

function buildReceiptNode(receipt: ConstitutionalReleaseReceipt, source: ConstitutionalEvidenceGraphSource): ConstitutionalEvidenceGraphNode {
  return {
    id: `receipt:${receipt.receiptId}`,
    kind: 'root-receipt',
    label: 'Constitutional Release Receipt',
    status: 'Verified',
    proofLevel: receipt.proofSurfaceLevel,
    source,
    verified: true,
    replayable: true,
    truthBoundary: receipt.truthBoundary,
    currentMaturity: receipt.constitutionalMaturity as ProofSurfaceOperationalStatus,
  };
}

function buildViewNodes(source: ConstitutionalEvidenceGraphSource, views: ConstitutionalEvidenceGraphView[]): ConstitutionalEvidenceGraphNode[] {
  return views.map((view) => ({
    id: view.id,
    kind: 'public-view',
    label: view.label,
    status: 'Observed',
    proofLevel: 'P1',
    source,
    verified: true,
    replayable: true,
    truthBoundary: 'A public view of the canonical evidence graph.',
  }));
}

function createSurfaceNodes(surface: ProofSurface, source: ConstitutionalEvidenceGraphSource): {
  proofSurfaceNode: ConstitutionalEvidenceGraphNode;
  claimNodes: ConstitutionalEvidenceGraphNode[];
  evidenceNodes: ConstitutionalEvidenceGraphNode[];
  claimResolutions: ConstitutionalEvidenceGraphClaimResolution[];
  unresolvedClaims: string[];
  edges: ConstitutionalEvidenceGraphEdge[];
} {
  const validation = validateProofSurface(surface);
  const proofSurfaceNode: ConstitutionalEvidenceGraphNode = {
    id: `surface:${surface.identity.id}`,
    kind: 'proof-surface',
    label: surface.identity.name,
    status: validation.passed ? 'Verified' : 'Hypothesized',
    proofLevel: surface.proofLevel,
    source,
    verified: validation.passed,
    replayable: surface.replayStatus !== 'NotAvailable',
    truthBoundary: surface.truthBoundary,
    currentMaturity: surface.constitutionalProfile.currentMaturity,
    commercialReadiness: surface.commercialReadiness,
    proofSurfaceId: surface.identity.id,
  };

  const claimNodes: ConstitutionalEvidenceGraphNode[] = [];
  const evidenceNodes: ConstitutionalEvidenceGraphNode[] = [];
  const claimResolutions: ConstitutionalEvidenceGraphClaimResolution[] = [];
  const unresolvedClaims: string[] = [];
  const edges: ConstitutionalEvidenceGraphEdge[] = [];

  for (const claim of surface.claims) {
    const claimLevel = claim.proofLevel ?? minProofLevelForClaimType(claim.type);
    const claimIssues = validation.issues.filter(
      (issue) => issue.field.startsWith(`claims.${claim.id}`) && issue.severity === 'error',
    );
    const claimReplayable = claim.evidenceIds.every((evidenceId) => {
      const evidence = surface.evidence.find((entry) => entry.id === evidenceId);
      return evidence ? evidence.replayable : false;
    });
    const claimVerified = claimIssues.length === 0;
    const claimNodeId = `claim:${surface.identity.id}:${claim.id}`;

    claimNodes.push({
      id: claimNodeId,
      kind: 'claim',
      label: claim.statement,
      status: claimVerified ? 'Verified' : 'Hypothesized',
      proofLevel: claimLevel,
      source,
      verified: claimVerified,
      replayable: claimReplayable,
      truthBoundary: surface.truthBoundary,
      proofSurfaceId: surface.identity.id,
      claimId: claim.id,
      claimType: claim.type,
    });

    edges.push({
      id: `edge:${proofSurfaceNode.id}->${claimNodeId}`,
      from: proofSurfaceNode.id,
      to: claimNodeId,
      relation: 'contains',
    });

    for (const evidenceId of claim.evidenceIds) {
      const evidence = surface.evidence.find((entry) => entry.id === evidenceId);
      if (!evidence) {
        unresolvedClaims.push(`${surface.identity.id}:${claim.id}:${evidenceId}`);
        continue;
      }

      const evidenceNodeId = `evidence:${surface.identity.id}:${evidence.id}`;
      const evidenceNode: ConstitutionalEvidenceGraphNode = {
        id: evidenceNodeId,
        kind: 'evidence',
        label: evidence.statement,
        status: evidence.replayable ? 'Observed' : 'Hypothesized',
        proofLevel: evidence.proofLevel,
        source,
        verified: evidence.verificationStatus !== 'Implemented' || evidence.replayable,
        replayable: evidence.replayable,
        truthBoundary: surface.truthBoundary,
        proofSurfaceId: surface.identity.id,
        claimId: claim.id,
        evidenceId: evidence.id,
      };
      evidenceNodes.push(evidenceNode);
      edges.push({
        id: `edge:${claimNodeId}->${evidenceNodeId}`,
        from: claimNodeId,
        to: evidenceNodeId,
        relation: 'supports',
      });
    }

    if (!claimVerified) {
      unresolvedClaims.push(`${surface.identity.id}:${claim.id}`);
    }

    claimResolutions.push({
      claimId: claim.id,
      claimType: claim.type,
      proofSurfaceId: surface.identity.id,
      evidenceIds: [...claim.evidenceIds],
      proofLevel: claimLevel,
      verified: claimVerified,
      replayable: claimReplayable,
      issues: claimIssues.map((issue) => `${issue.field}: ${issue.message}`),
    });
  }

  return {
    proofSurfaceNode,
    claimNodes,
    evidenceNodes,
    claimResolutions,
    unresolvedClaims,
    edges,
  };
}

export function createConstitutionalEvidenceGraph(
  receipt: ConstitutionalReleaseReceipt,
  surfaces: readonly ProofSurface[],
  options: {
    source?: ConstitutionalEvidenceGraphSource;
    generatedAt?: string;
    views?: ConstitutionalEvidenceGraphView[];
  } = {},
): ConstitutionalEvidenceGraph {
  const generatedAt = options.generatedAt ?? receipt.generatedAt ?? new Date().toISOString();
  const source = options.source ?? 'release-receipt';
  const views = (options.views ?? VIEW_DEFINITIONS).map((view) => ({ ...view }));
  const rootReceipt = stripReceiptGraph(receipt);
  const receiptNode = buildReceiptNode(rootReceipt, source);

  const proofSurfaces: ConstitutionalEvidenceGraphProofSurface[] = [];
  const claimResolutions: ConstitutionalEvidenceGraphClaimResolution[] = [];
  const unresolvedClaims: string[] = [];
  const nodes: ConstitutionalEvidenceGraphNode[] = [receiptNode];
  const edges: ConstitutionalEvidenceGraphEdge[] = [];

  for (const view of views) {
    nodes.push({
      id: view.id,
      kind: 'public-view',
      label: view.label,
      status: 'Observed',
      proofLevel: 'P1',
      source,
      verified: true,
      replayable: true,
      truthBoundary: 'A public view of the canonical evidence graph.',
    });
    edges.push({
      id: `edge:${receiptNode.id}->${view.id}`,
      from: receiptNode.id,
      to: view.id,
      relation: 'publishes',
    });
  }

  for (const surface of surfaces) {
    const surfaceResult = createSurfaceNodes(surface, source);
    nodes.push(surfaceResult.proofSurfaceNode, ...surfaceResult.claimNodes, ...surfaceResult.evidenceNodes);
    edges.push(
      {
        id: `edge:${receiptNode.id}->${surfaceResult.proofSurfaceNode.id}`,
        from: receiptNode.id,
        to: surfaceResult.proofSurfaceNode.id,
        relation: 'roots',
      },
      ...surfaceResult.edges,
    );

    proofSurfaces.push({
      proofSurfaceId: surface.identity.id,
      proofLevel: surface.proofLevel,
      verificationStatus: surface.verificationStatus,
      replayStatus: surface.replayStatus,
      operationalStatus: surface.operationalStatus,
      truthBoundary: surface.truthBoundary,
      currentMaturity: surface.constitutionalProfile.currentMaturity,
      commercialReadiness: surface.commercialReadiness,
      nextRequiredEvidence: [...surface.nextRequiredEvidence],
    });
    claimResolutions.push(...surfaceResult.claimResolutions);
    unresolvedClaims.push(...surfaceResult.unresolvedClaims);
  }

  const publicClaimIds = claimResolutions.map((entry) => entry.claimId);
  const publicProofSurfaceIds = proofSurfaces.map((entry) => entry.proofSurfaceId);
  const resolvedViews = views.map((view) => ({
    ...view,
    claimIds: [...publicClaimIds],
    proofSurfaceIds: [...publicProofSurfaceIds],
  }));

  nodes.push(...buildViewNodes(source, resolvedViews));
  for (const view of resolvedViews) {
    edges.push({
      id: `edge:${receiptNode.id}->${view.id}`,
      from: receiptNode.id,
      to: view.id,
      relation: 'publishes',
    });
  }

  const summary: ConstitutionalEvidenceGraphSummary = {
    graphId: `ceg:${rootReceipt.receiptId}`,
    rootReceiptId: rootReceipt.receiptId,
    source,
    proofSurfaceCount: proofSurfaces.length,
    claimCount: claimResolutions.length,
    verifiedClaimCount: claimResolutions.filter((entry) => entry.verified).length,
    replayableClaimCount: claimResolutions.filter((entry) => entry.replayable).length,
    unresolvedClaims: [...unresolvedClaims],
    viewCount: views.length,
  };

  return {
    schemaVersion: CONSTITUTIONAL_EVIDENCE_GRAPH_JSON_SCHEMA_VERSION,
    graphId: summary.graphId,
    generatedAt,
    source,
    rootReceipt,
    proofSurfaces,
    claims: claimResolutions,
    views: resolvedViews,
    nodes,
    edges,
    unresolvedClaims: [...unresolvedClaims],
    summary,
  };
}

export function createConstitutionalEvidenceGraphFromProofSurfaces(
  surfaces: readonly ProofSurface[],
  options: {
    source?: ConstitutionalEvidenceGraphSource;
    generatedAt?: string;
    views?: ConstitutionalEvidenceGraphView[];
  } = {},
): ConstitutionalEvidenceGraph {
  const generatedAt = options.generatedAt ?? new Date().toISOString();
  const receipt = makeSyntheticReceipt(surfaces, generatedAt);
  return createConstitutionalEvidenceGraph(receipt, surfaces, {
    ...options,
    source: options.source ?? 'local-registry',
    generatedAt,
  });
}

export function validateConstitutionalEvidenceGraph(graph: ConstitutionalEvidenceGraph): ConstitutionalEvidenceGraphValidationIssue[] {
  const issues: ConstitutionalEvidenceGraphValidationIssue[] = [];
  const proofSurfaceById = new Map(graph.proofSurfaces.map((surface) => [surface.proofSurfaceId, surface] as const));
  const proofSurfaceNodesById = new Map(
    graph.nodes
      .filter((node) => node.kind === 'proof-surface' && typeof node.proofSurfaceId === 'string')
      .map((node) => [node.proofSurfaceId as string, node] as const),
  );
  const claimById = new Map(graph.claims.map((claim) => [claim.claimId, claim] as const));

  if (!graph.rootReceipt?.receiptId) {
    issues.push({ scope: 'receipt', field: 'receipt', message: 'missing root receipt', severity: 'error' });
  }
  if (!graph.nodes.some((node) => node.kind === 'root-receipt')) {
    issues.push({ scope: 'graph', field: 'graph', message: 'graph is missing a receipt root node', severity: 'error' });
  }
  if (graph.rootReceipt && graph.rootReceipt.constitutionalEvidenceGraph != null) {
    issues.push({
      scope: 'receipt',
      field: 'receipt',
      message: 'root receipt must not embed another constitutional evidence graph',
      severity: 'error',
    });
  }
  if (graph.proofSurfaces.length === 0) {
    issues.push({ scope: 'graph', field: 'graph', message: 'graph does not contain any proof surfaces', severity: 'error' });
  }
  if (graph.claims.length === 0) {
    issues.push({ scope: 'graph', field: 'graph', message: 'graph does not contain any claim resolutions', severity: 'error' });
  }

  for (const claim of graph.claims) {
    if (!claim.verified) {
      issues.push({ scope: 'claim', field: 'claim', message: `claim ${claim.claimId} is not verified`, severity: 'error' });
    }
    if (!claim.proofSurfaceId) {
      issues.push({ scope: 'claim', field: 'claim', message: `claim ${claim.claimId} is not linked to a proof surface`, severity: 'error' });
    } else {
      const proofSurface = proofSurfaceById.get(claim.proofSurfaceId);
      const proofSurfaceNode = proofSurfaceNodesById.get(claim.proofSurfaceId);

      if (!proofSurface) {
        issues.push({
          scope: 'claim',
          field: 'claim',
          message: `claim ${claim.claimId} references an unknown proof surface ${claim.proofSurfaceId}`,
          severity: 'error',
        });
      }
      if (!proofSurfaceNode) {
        issues.push({
          scope: 'claim',
          field: 'claim',
          message: `claim ${claim.claimId} does not resolve to a proof-surface node`,
          severity: 'error',
        });
      } else if (!proofSurfaceNode.verified) {
        issues.push({
          scope: 'claim',
          field: 'claim',
          message: `claim ${claim.claimId} does not resolve to a verifiable proof surface`,
          severity: 'error',
        });
      } else if (proofLevelRank(claim.proofLevel) > proofLevelRank(proofSurfaceNode.proofLevel)) {
        issues.push({
          scope: 'claim',
          field: 'claim',
          message: `claim ${claim.claimId} exceeds proof surface level ${proofSurfaceNode.proofLevel}`,
          severity: 'error',
        });
      }
    }
    if (claim.evidenceIds.length === 0) {
      issues.push({ scope: 'claim', field: 'claim', message: `claim ${claim.claimId} does not resolve to evidence`, severity: 'error' });
    }

    if (!graph.views.some((view) => view.claimIds.includes(claim.claimId))) {
      issues.push({
        scope: 'claim',
        field: 'claim',
        message: `claim ${claim.claimId} is not published through a public view`,
        severity: 'error',
      });
    }

    for (const evidenceId of claim.evidenceIds) {
      const evidenceNode = graph.nodes.find(
        (node) => node.kind === 'evidence' && node.evidenceId === evidenceId && node.claimId === claim.claimId,
      );

      if (!evidenceNode) {
        issues.push({
          scope: 'claim',
          field: 'claim',
          message: `claim ${claim.claimId} does not resolve evidence node ${evidenceId}`,
          severity: 'error',
        });
        continue;
      }

      if (evidenceNode.proofSurfaceId !== claim.proofSurfaceId) {
        issues.push({
          scope: 'claim',
          field: 'claim',
          message: `claim ${claim.claimId} resolves evidence ${evidenceId} from a different proof surface`,
          severity: 'error',
        });
      }

      if (!evidenceNode.verified) {
        issues.push({
          scope: 'claim',
          field: 'claim',
          message: `claim ${claim.claimId} resolves to unverified evidence ${evidenceId}`,
          severity: 'error',
        });
      }
    }
  }

  for (const view of graph.views) {
    if (view.claimIds.length === 0) {
      issues.push({ scope: 'graph', field: 'graph', message: `view ${view.id} does not reference any public claims`, severity: 'error' });
    }
    if (view.proofSurfaceIds.length === 0) {
      issues.push({ scope: 'graph', field: 'graph', message: `view ${view.id} does not reference any proof surfaces`, severity: 'error' });
    }

    for (const claimId of view.claimIds) {
      if (!claimById.has(claimId)) {
        issues.push({
          scope: 'graph',
          field: 'graph',
          message: `view ${view.id} references an unknown claim ${claimId}`,
          severity: 'error',
        });
      }
    }

    for (const proofSurfaceId of view.proofSurfaceIds) {
      const proofSurfaceNode = proofSurfaceNodesById.get(proofSurfaceId);
      if (!proofSurfaceNode) {
        issues.push({
          scope: 'graph',
          field: 'graph',
          message: `view ${view.id} references an unknown proof surface ${proofSurfaceId}`,
          severity: 'error',
        });
      } else if (!proofSurfaceNode.verified) {
        issues.push({
          scope: 'graph',
          field: 'graph',
          message: `view ${view.id} references an unverified proof surface ${proofSurfaceId}`,
          severity: 'error',
        });
      }
    }
  }

  if (graph.unresolvedClaims.length > 0) {
    issues.push({ scope: 'graph', field: 'graph', message: `graph has unresolved claims: ${graph.unresolvedClaims.join(', ')}`, severity: 'error' });
  }

  if (graph.summary.rootReceiptId !== graph.rootReceipt.receiptId) {
    issues.push({ scope: 'receipt', field: 'receipt', message: 'graph summary root does not match receipt id', severity: 'error' });
  }
  if (graph.summary.proofSurfaceCount !== graph.proofSurfaces.length) {
    issues.push({ scope: 'graph', field: 'graph', message: 'graph summary proof-surface count is inconsistent', severity: 'error' });
  }
  if (graph.summary.claimCount !== graph.claims.length) {
    issues.push({ scope: 'graph', field: 'graph', message: 'graph summary claim count is inconsistent', severity: 'error' });
  }
  if (graph.summary.unresolvedClaims.length !== graph.unresolvedClaims.length) {
    issues.push({ scope: 'graph', field: 'graph', message: 'graph summary unresolved-claim count is inconsistent', severity: 'error' });
  }

  return issues;
}

export function summarizeConstitutionalEvidenceGraph(graph: ConstitutionalEvidenceGraph): ConstitutionalEvidenceGraphSummary {
  return clone(graph.summary);
}

export function resolveConstitutionalEvidenceGraph(
  receipt: ConstitutionalReleaseReceipt,
  surfaces: readonly ProofSurface[],
  options: {
    source?: ConstitutionalEvidenceGraphSource;
    generatedAt?: string;
    views?: ConstitutionalEvidenceGraphView[];
  } = {},
): ConstitutionalEvidenceGraph {
  const graph = createConstitutionalEvidenceGraph(receipt, surfaces, options);
  const issues = validateConstitutionalEvidenceGraph(graph);
  if (issues.some((issue) => issue.severity === 'error')) {
    const messages = issues.map((issue) => `${issue.scope}.${issue.field}: ${issue.message}`).join('; ');
    throw new Error(`constitutional evidence graph validation failed: ${messages}`);
  }
  return graph;
}

export function resolveConstitutionalEvidenceGraphFromProofSurfaces(
  surfaces: readonly ProofSurface[],
  options: {
    source?: ConstitutionalEvidenceGraphSource;
    generatedAt?: string;
    views?: ConstitutionalEvidenceGraphView[];
  } = {},
): ConstitutionalEvidenceGraph {
  return resolveConstitutionalEvidenceGraphFromProofSurfacesUnsafe(surfaces, options);
}

export function resolveConstitutionalEvidenceGraphFromReleaseReceipt(
  receipt: ConstitutionalReleaseReceipt,
  surfaces: readonly ProofSurface[],
  options: {
    source?: ConstitutionalEvidenceGraphSource;
    generatedAt?: string;
    views?: ConstitutionalEvidenceGraphView[];
  } = {},
): ConstitutionalEvidenceGraph {
  return resolveConstitutionalEvidenceGraph(receipt, surfaces, {
    ...options,
    source: options.source ?? 'release-receipt',
  });
}

function resolveConstitutionalEvidenceGraphFromProofSurfacesUnsafe(
  surfaces: readonly ProofSurface[],
  options: {
    source?: ConstitutionalEvidenceGraphSource;
    generatedAt?: string;
    views?: ConstitutionalEvidenceGraphView[];
  } = {},
): ConstitutionalEvidenceGraph {
  const graph = createConstitutionalEvidenceGraphFromProofSurfaces(surfaces, options);
  const issues = validateConstitutionalEvidenceGraph(graph);
  if (issues.some((issue) => issue.severity === 'error')) {
    const messages = issues.map((issue) => `${issue.scope}.${issue.field}: ${issue.message}`).join('; ');
    throw new Error(`constitutional evidence graph validation failed: ${messages}`);
  }
  return graph;
}
