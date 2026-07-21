import {
  createDemoProofSurfaceRegistry,
  createConstitutionalEvidenceGraphFromProofSurfaces,
  listProofSurfaceSummaries,
  type ConstitutionalEvidenceGraph,
  type ConstitutionalEvidenceGraphSummary,
  type ProofSurface,
  type ProofSurfaceSummary,
} from '@aaes-os/aaes-governance';

import {
  DEFAULT_PROOF_SURFACE_CATALOG_URL,
  isLocalProofSurfaceCatalogUrl,
} from './catalogConfig';

export type ProofSurfaceCatalogSource = 'operator-backend' | 'local-registry';

export interface LoadedNovaStudioProofSurfaces {
  source: ProofSurfaceCatalogSource;
  catalogUrl: string;
  surfaces: ProofSurfaceSummary[];
  replayableSurfaces: ProofSurface[];
  graph: ConstitutionalEvidenceGraphSummary;
}

export interface NovaStudioProofSurfaceCatalog {
  summaries?: ProofSurfaceSummary[];
  records?: unknown[];
  catalog?: {
    surfaces?: Array<{ surface?: unknown }>;
  };
}

export async function loadNovaStudioProofSurfaces(
  catalogUrl = DEFAULT_PROOF_SURFACE_CATALOG_URL,
): Promise<LoadedNovaStudioProofSurfaces> {
  if (isLocalProofSurfaceCatalogUrl(catalogUrl)) {
    const registry = createDemoProofSurfaceRegistry();
    registry.publish(sovereignxRouterProofSurface);
    const graph = createConstitutionalEvidenceGraphFromProofSurfaces(registry.list(), {
      source: 'local-registry',
    });
    return {
      source: 'local-registry',
      catalogUrl,
      surfaces: listProofSurfaceSummaries(registry).map((surface) => ({ ...surface })),
      replayableSurfaces: registry.list(),
      graph: graph.summary,
    };
  }

  const [liveCatalog, liveGraph] = await Promise.all([
    loadLiveProofSurfaceCatalog(catalogUrl),
    loadLiveEvidenceGraph(catalogUrl),
  ]);
  if (liveCatalog) {
    const graph = liveGraph ?? createConstitutionalEvidenceGraphFromProofSurfaces(createDemoProofSurfaceRegistry().list(), {
      source: 'local-registry',
    });
    return {
      source: 'operator-backend',
      catalogUrl,
      surfaces: liveCatalog,
      replayableSurfaces: [],
      graph: graph.summary,
    };
  }

  const registry = createDemoProofSurfaceRegistry();
  registry.publish(sovereignxRouterProofSurface);
  const graph = createConstitutionalEvidenceGraphFromProofSurfaces(registry.list(), {
    source: 'local-registry',
  });
  return {
    source: 'local-registry',
    catalogUrl,
    surfaces: listProofSurfaceSummaries(registry).map((surface) => ({ ...surface })),
    replayableSurfaces: registry.list(),
    graph: graph.summary,
  };
}

async function loadLiveProofSurfaceCatalog(
  catalogUrl: string,
): Promise<ProofSurfaceSummary[] | null> {
  try {
    const response = await fetch(catalogUrl, {
      headers: {
        accept: 'application/json',
      },
    });
    if (!response.ok) {
      return null;
    }
    const payload = (await response.json()) as NovaStudioProofSurfaceCatalog;
    if (Array.isArray(payload.summaries) && payload.summaries.length > 0) {
      return payload.summaries;
    }
    if (payload.catalog?.surfaces?.length) {
      return payload.catalog.surfaces
        .map((entry) => entry.surface)
        .filter(isProofSurfaceSummary) as ProofSurfaceSummary[];
    }
    return null;
  } catch {
    return null;
  }
}

async function loadLiveEvidenceGraph(catalogUrl: string): Promise<ConstitutionalEvidenceGraphSummary | null> {
  const graphUrl = resolveEvidenceGraphUrl(catalogUrl);
  if (!graphUrl) {
    return null;
  }

  try {
    const response = await fetch(graphUrl, {
      headers: {
        accept: 'application/json',
      },
    });
    if (!response.ok) {
      return null;
    }
    const payload = (await response.json()) as {
      summary?: ConstitutionalEvidenceGraphSummary;
      graph?: ConstitutionalEvidenceGraph;
    };
    if (payload.summary) {
      return payload.summary;
    }
    if (payload.graph?.summary) {
      return payload.graph.summary;
    }
    return null;
  } catch {
    return null;
  }
}

function resolveEvidenceGraphUrl(catalogUrl: string): string | null {
  if (isLocalProofSurfaceCatalogUrl(catalogUrl)) {
    return null;
  }
  try {
    const url = new URL(catalogUrl, typeof window === 'undefined' ? 'http://127.0.0.1' : window.location.href);
    if (url.pathname.endsWith('/proof-surfaces')) {
      url.pathname = url.pathname.replace(/\/proof-surfaces$/, '/evidence-graph');
    } else if (!url.pathname.endsWith('/evidence-graph')) {
      url.pathname = `${url.pathname.replace(/\/$/, '')}/evidence-graph`;
    }
    return url.toString();
  } catch {
    return null;
  }
}

function isProofSurfaceSummary(value: unknown): value is ProofSurfaceSummary {
  return Boolean(
    value &&
      typeof value === 'object' &&
      'identity' in value &&
      'proofLevel' in value &&
      'commercialReadiness' in value,
  );
}

const sovereignxRouterProofSurface: ProofSurface = {
  identity: {
    id: '@aaes-os/sovereignx-router',
    name: 'SovereignX Router',
    type: 'implementation',
    version: '0.1.0',
  },
  purpose: 'Route governed compute work across CPU and GPU under CIEMS constraints.',
  claims: [
    {
      id: 'nova-router-cpu-governs-gpu',
      type: 'Architectural',
      statement: 'CPU governs scheduling, continuity, and policy while GPU receives only allowed workloads.',
      evidenceIds: ['nova-router-evidence-tests'],
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayStatus: 'Replayable',
      operationalStatus: 'Prototype',
    },
    {
      id: 'nova-router-ciems-policy',
      type: 'Specification',
      statement: 'CIEMS decisions can throttle, quarantine, kill, or allow governed compute tasks.',
      evidenceIds: ['nova-router-evidence-tests'],
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayStatus: 'Replayable',
      operationalStatus: 'Prototype',
    },
  ],
  evidence: [
    {
      id: 'nova-router-evidence-tests',
      statement: 'Nova Studio can render and inspect the router proof-surface record in local registry mode.',
      proofLevel: 'P2',
      verificationStatus: 'Test Verified',
      replayable: true,
      verifiedBy: 'nova-studio/src/components/StudioApp.tsx',
    },
  ],
  verificationStatus: 'Implemented',
  proofLevel: 'P2',
  replayStatus: 'Replayable',
  operationalStatus: 'Prototype',
  truthBoundary: 'Proves governed routing and policy evaluation, not production-scale cluster orchestration.',
  constitutionalProfile: {
    purpose: 'Govern CPU vs GPU dispatch under constitutional constraints.',
    authority: 'AAES governance law, proof-surface law, and CIEMS policy contracts.',
    evidenceModel: 'Routing decisions, CIEMS decisions, evidence records, and tests.',
    verificationProcess: 'Build, test, replay the router proof-surface view, and validate the data contract.',
    complianceRequirements: ['No claim may exceed evidence', 'CPU governs policy', 'GPU remains an accelerator'],
    truthBoundary: 'This package proves governed routing, not full cluster management.',
    constitutionalScope: 'Compute routing, governance enforcement, and measurement health.',
    constitutionalLimits: 'It does not claim full hardware management or multi-node scheduling.',
    dependencies: ['AAES governance package'],
    stewardship: 'Nova Studio maintainers',
    replayPath: 'Replay the local registry snapshot and operator catalog rendering.',
    failurePath: 'Fallback to seeded registry data when the backend is unavailable.',
    currentMaturity: 'Prototype',
  },
  blindspots: ['No real GPU telemetry adapter yet', 'No thermal sensor integration yet'],
  battleScars: ['Router ideas can overclaim before telemetry exists'],
  adversarialClaims: ['A studio screenshot can be mistaken for authoritative evidence'],
  colorTeamReadiness: {
    redTeam: 'Attack surface is bounded by explicit routing evidence.',
    blueTeam: 'Imported records can be inspected deterministically.',
    purpleTeam: 'UI and registry claims can be reconciled.',
    greenTeam: 'Build and test are repeatable in local registry mode.',
    yellowTeam: 'Operator messaging is clear, but the package is still a prototype.',
    whiteTeam: 'Constitutional authority is explicit and machine-readable.',
  },
  commercialReadiness: {
    targetTier: 'Builder',
    intendedCustomer: 'Operators, reviewers, and contributors',
    primaryUseCase: 'Proof-surface visualization and review',
    valueProposition: 'A clear UI for claim/evidence maturity.',
    currentReadiness: 'Prototype',
  },
  nextRequiredEvidence: ['Live backend proof-surface ingestion', 'Multi-node operator demo'],
};
