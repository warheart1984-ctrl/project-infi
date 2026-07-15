import express from 'express';
import type { Express } from 'express';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { DriftMetrics, type ProofSurface } from '@aaes-os/aaes-governance';
import {
  createDemoProofSurfaceRegistry,
  createConstitutionalEvidenceGraphFromProofSurfaces,
  createProofSurfaceCatalogDocument,
  listProofSurfaceSummaries,
  resolveConstitutionalEvidenceGraphFromReleaseReceipt,
  summarizeConstitutionalEvidenceGraph,
  type ConstitutionalEvidenceGraph,
  type ConstitutionalReleaseReceipt,
} from '@aaes-os/aaes-governance';
import { createCenDemoResult, type EnforcementReceipt } from '@aaes-os/constitutional-enforcement-node';
import {
  evaluateInvariantFitness,
  proposeInvariant,
} from '@aaes-os/constitutional-evolution';
import {
  collapseGovernanceLayers,
  createLawOfLawsLedger,
  recordMetaConstitutionalCollapsePod,
} from '@aaes-os/meta-constitutional-calculus';
import { forecastTrajectory } from '@aaes-os/nimf';
import {
  appendSovereigntyEntry,
  createSovereigntyLedger,
} from '@aaes-os/sovereignty-ledger';
import {
  createSovereignXScaffold,
  createSovereignXHardwareGovernor,
  SovereignXRouter,
  routeSovereignXClusterWork,
  type SovereignXExecutionProofSurface,
  type SovereignXClusterRouteRequest,
  type SovereignXClusterNode,
} from '@aaes-os/sovereignx-router';
import {
  createPricingLedgerEntryResponse,
  renderPricingCohortHistoryCsv,
  renderPricingMarginReportCsv,
  summarizePricingLedger,
} from './pricingLedger.js';
import { getCoriAlphaWorkspaceSummary } from '@aaes-os/platform-core';

import { createArenaModeSnapshot } from './arenaMode.js';
import {
  approvePatch,
  deployPatch,
  listPatches,
  rejectPatch,
} from './patchLedgerState.js';
import { getSeededMriAssessment, getSeededMriAssessmentV2 } from './mriState.js';
import {
  ensureTelemetrySeeded,
  faultJournal,
  patchAnalytics,
  patternLedger,
} from './telemetryState.js';
import { getSubsystemCoverage } from './coverageState.js';
import { getCabTelemetrySummary } from './cabTelemetry.js';
import { getAaisTelemetryStatus } from './aaisBridge.js';
import { GovernanceAdapter } from './GovernanceAdapter.js';
import { LedgerAdapter } from './LedgerAdapter.js';
import { FaultAdapter } from './FaultAdapter.js';
import { RuntimeAdapter } from './RuntimeAdapter.js';
import { SubstrateAdapter } from './SubstrateAdapter.js';
import {
  createSovereignXHardwareTelemetryAdapter,
  type SovereignXHardwareSnapshot,
} from './SovereignXHardwareTelemetryAdapter.js';
import {
  createSovereignXHardwareReplayStore,
} from './sovereignxHardwareReplayStore.js';
import { createHardwareEvidenceStore } from './hardwareEvidenceStore.js';
import {
  buildHardwareBenchmarkCatalog,
  buildHardwareConsoleSummary,
  buildHardwareReplayComparison,
  estimateHardwareBenchmarkMetrics,
  type HardwareBenchmarkRunArtifact,
  type HardwareConsoleSummary,
  type HardwareReplayArtifact,
  type HardwareRoute,
} from './hardwareConsole.js';
import {
  createCepArtifactStore,
  type CepArtifactKind,
  type CepArtifactRecord,
  verifyCepArtifactSignature,
} from './cepArtifactStore.js';
import { createSovereignXHardwareThermalBridge } from './sovereignxHardwareThermalBridge.js';
import { runSovereignXHardwareOverrideDrill, type SovereignXHardwareOverrideDrillRequest } from './sovereignxHardwareOverrideDrill.js';
import { validateSovereignXHardwareReplayRecords } from './sovereignxHardwareReplayValidation.js';
import {
  applySovereignXClusterControlRequest,
  buildSovereignXClusterGovernanceProjection,
  getSovereignXClusterControlState,
  resetSovereignXClusterControlState,
  type SovereignXClusterControlRequest,
  type SovereignXClusterGovernanceProjection,
} from './sovereignxClusterGovernance.js';

const PORT = Number(process.env.PORT ?? 4000);
const serviceDir = path.dirname(fileURLToPath(import.meta.url));
const clientDistDir = path.resolve(serviceDir, '..', 'dist', 'client');
const releaseReceiptPath = path.resolve(serviceDir, '..', '..', '..', 'release', 'constitutional-release-receipt.json');

ensureTelemetrySeeded();

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function roundTo(value: number, digits: number): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

const seededCenResult = createCenDemoResult();
const sovereigntyLedger = createSovereigntyLedger();
appendSovereigntyEntry(sovereigntyLedger, {
  eventType: 'denied_transition',
  subjectId: seededCenResult.receipt.transitionId,
  payload: seededCenResult.receipt,
  issuedAt: seededCenResult.receipt.issuedAt,
});
const lawOfLawsLedger = createLawOfLawsLedger();
lawOfLawsLedger.append({
  entryType: 'collapse_record',
  subjectId: 'CML-15',
  payload: collapseGovernanceLayers(),
  issuedAt: '2026-06-18T22:02:00.000Z',
});
lawOfLawsLedger.append({
  entryType: 'pod',
  subjectId: 'meta_constitutional_collapse',
  payload: recordMetaConstitutionalCollapsePod(),
  issuedAt: '2026-06-18T22:02:01.000Z',
});
const cenReceipts = new Map<string, EnforcementReceipt>([
  [seededCenResult.receipt.receiptId, seededCenResult.receipt],
]);

type GovernanceEvolutionTimelineEntry = {
  eventId: string;
  stage: 'birth' | 'growth' | 'governance' | 'replay' | 'renewal';
  artifactId: string;
  createdAt: string;
  summary: string;
  outcome: 'proposed' | 'replayed' | 'amended' | 'validated';
  continuityReport: {
    reportId: string;
    createdAt: string;
    valid: boolean;
    lineageValid: boolean;
    replayValid: boolean;
    receiptId: string;
    notes: string[];
    chain: {
      sequence: number;
      entryType: string;
      subjectId: string;
      issuedAt: string;
      entryHash: string;
      previousHash: string | null;
    }[];
  };
  governanceDiff: null | {
    diffId: string;
    createdAt: string;
    currentConfigVersion: string;
    targetConfigVersion: string;
    domain: string;
    tier: string;
    changes: {
      path: string;
      before: unknown;
      after: unknown;
      rationale: string;
    }[];
    replayReportIds: string[];
    trustReportIds: string[];
  };
  replayReport: null | {
    replayId: string;
    mode: 'Genesis' | 'Resonance' | 'Sacrifice';
    decision: 'promote' | 'retain' | 'revert';
    stage: 'soft' | 'constitutional' | 'reverted';
    summary: string;
    receiptId: string;
    lawOfLawsEntryId: string;
  };
};

type GovernanceEvolutionTimeline = {
  timelineId: string;
  entries: GovernanceEvolutionTimelineEntry[];
  summary: {
    entryCount: number;
    continuityReports: number;
    governanceDiffs: number;
    replayReports: number;
    validatedAmendments: number;
  };
};

type SovereignXHardwareBenchmarkScenario = {
  scenarioId: string;
  label: string;
  backend: string;
  nodeId: string | null;
  nodeRole: 'CPU' | 'GPU' | 'MIXED' | null;
  estimatedLatencyMs: number;
  estimatedThroughputOpsPerSec: number;
  estimatedCostIndex: number;
  estimatedThermalHeadroomC: number;
  estimatedThrottleRisk: number;
  notes: string[];
};

type SovereignXHardwareBenchmarkComparison = {
  metric: string;
  baseline: number;
  governed: number;
  delta: number;
  deltaPct: number;
};

type SovereignXHardwareBenchmarks = {
  available: boolean;
  generatedAtMs: number;
  source: string;
  sourceDetail: string;
  currentDecision: string;
  baselineScenario: SovereignXHardwareBenchmarkScenario;
  governedScenario: SovereignXHardwareBenchmarkScenario;
  counterfactualScenarios: SovereignXHardwareBenchmarkScenario[];
  comparisons: SovereignXHardwareBenchmarkComparison[];
  summary: {
    estimatedLatencyReductionPct: number;
    estimatedThroughputGainPct: number;
    estimatedCostEfficiencyGainPct: number;
    thermalHeadroomDeltaC: number;
    recommendation: string;
  };
};

const governanceEvolutionTimeline = buildGovernanceEvolutionTimeline();

const governanceAdapter = new GovernanceAdapter(faultJournal.getAll());
const ledgerAdapter = new LedgerAdapter(listPatches);
const faultAdapter = new FaultAdapter(faultJournal);
const runtimeAdapter = new RuntimeAdapter(() => false);
const substrateAdapter = new SubstrateAdapter(() => false);
const sovereignXHardwareTelemetryAdapter = createSovereignXHardwareTelemetryAdapter();
const sovereignXThermalBridge = createSovereignXHardwareThermalBridge();
const sovereignXHardwareGovernor = createSovereignXHardwareGovernor({
  clock: () => Date.now(),
  authority: 'SovereignX.Router',
});
const sovereignXHardwareReplayStore = createSovereignXHardwareReplayStore();
const hardwareEvidenceStore = createHardwareEvidenceStore();
const cepArtifactStore = createCepArtifactStore();
const CEP_ARTIFACT_KINDS: CepArtifactKind[] = ['promotion-request', 'replay-job', 'decision'];
let cepViewState: CepViewState = {
  selectedKind: 'decision',
  selectedArtifactId: null,
  updatedAt: new Date().toISOString(),
  source: 'local',
};
seedCepArtifactsIfNeeded();
cepViewState = buildInitialCepViewState();
resetSovereignXClusterControlState();
const platformApiBaseUrl = (process.env.PLATFORM_API_URL ?? 'http://localhost:4100').replace(/\/+$/, '');
let platformApiSessionIdPromise: Promise<string | null> | null = null;

const app: Express = express();
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
      id: 'ops-router-cpu-governs-gpu',
      type: 'Architectural',
      statement: 'CPU governs scheduling, continuity, and policy while GPU receives only allowed workloads.',
      evidenceIds: ['ops-router-evidence-tests', 'ops-router-evidence-surface'],
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayStatus: 'Replayable',
      operationalStatus: 'Verified Prototype',
    },
    {
      id: 'ops-router-ciems-policy',
      type: 'Specification',
      statement: 'CIEMS decisions can throttle, quarantine, kill, or allow governed compute tasks.',
      evidenceIds: ['ops-router-evidence-tests'],
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayStatus: 'Replayable',
      operationalStatus: 'Verified Prototype',
    },
    {
      id: 'ops-router-hardware-governor',
      type: 'Architectural',
      statement: 'A live hardware telemetry adapter feeds the SovereignX hardware governor and exposes promotion, retraction, and quarantine state.',
      evidenceIds: ['ops-router-evidence-tests', 'ops-router-evidence-hardware-governor'],
      proofLevel: 'P2',
      verificationStatus: 'Test Verified',
      replayStatus: 'Replayable',
      operationalStatus: 'Verified Prototype',
    },
  ],
  evidence: [
    {
      id: 'ops-router-evidence-tests',
      statement: 'Router tests exercise CPU/GPU fallback, throttling, quarantine, and proof-surface validation.',
      proofLevel: 'P2',
      verificationStatus: 'Test Verified',
      replayable: true,
      verifiedBy: 'services/ops-console/src/server.test.ts',
    },
    {
      id: 'ops-router-evidence-surface',
      statement: 'Proof surface records are machine-readable and published through the operator catalog.',
      proofLevel: 'P2',
      verificationStatus: 'Implemented',
      replayable: true,
      verifiedBy: 'services/ops-console/src/server.ts',
    },
    {
      id: 'ops-router-evidence-hardware-governor',
      statement: 'The ops console publishes a live SovereignX hardware snapshot and a dedicated hardware route backed by a telemetry adapter.',
      proofLevel: 'P2',
      verificationStatus: 'Test Verified',
      replayable: true,
      verifiedBy: 'services/ops-console/src/server.test.ts',
    },
  ],
  verificationStatus: 'Implemented',
  proofLevel: 'P2',
  replayStatus: 'Replayable',
  operationalStatus: 'Verified Prototype',
  truthBoundary: 'Proves governed routing, hardware snapshots, and policy evaluation, not production-scale cluster orchestration.',
  constitutionalProfile: {
    purpose: 'Govern CPU vs GPU dispatch under constitutional constraints and surface live hardware telemetry evidence.',
    authority: 'AAES governance law, proof-surface law, CIEMS policy contracts, and the SovereignX hardware governor contract.',
    evidenceModel: 'Routing decisions, hardware snapshots, CIEMS decisions, evidence records, and tests.',
    verificationProcess: 'Build, test, replay the router decisions, validate hardware telemetry, and validate the proof surface.',
    complianceRequirements: ['No claim may exceed evidence', 'CPU governs policy', 'GPU remains an accelerator', 'Telemetry must be validated before promotion'],
    truthBoundary: 'This package proves governed routing and hardware snapshots, not full cluster management.',
    constitutionalScope: 'Compute routing, governance enforcement, hardware snapshots, and measurement health.',
    constitutionalLimits: 'It does not claim full hardware management or multi-node scheduling.',
    dependencies: ['local proof surface law'],
    stewardship: 'AAES-OS governance maintainers',
    replayPath: 'Replay the evidence log and routing decisions from the router history.',
    failurePath: 'Throttle, quarantine, delay, or drop work when invariants fail.',
    currentMaturity: 'Verified Prototype',
  },
  blindspots: ['No multi-node orchestration yet', 'No vendor-specific thermal sensor bridge yet'],
  battleScars: ['Router ideas can overclaim before telemetry exists', 'Policy and acceleration layers can be confused without a proof surface'],
  adversarialClaims: [
    'An attacker could claim GPU work was routed safely without evidence',
    'A stale measurement feed could be mistaken for trustworthy telemetry',
  ],
  colorTeamReadiness: {
    redTeam: 'Attack surface is bounded by explicit routing decisions and evidence records.',
    blueTeam: 'Policy decisions are logged, but real hardware telemetry is still stubbed.',
    purpleTeam: 'Combined attack/defense tests are possible through deterministic router evaluation.',
    greenTeam: 'Build and test are expected to be stable within the workspace package.',
    yellowTeam: 'Operator messaging is clear, but the package is still a prototype.',
    whiteTeam: 'Constitutional authority is explicit and machine-readable.',
  },
  commercialReadiness: {
    targetTier: 'Builder',
    intendedCustomer: 'Developers and platform operators building governed compute runtimes.',
    primaryUseCase: 'Resource fairness and constitutional routing for agentic workloads.',
    valueProposition: 'Makes CPU policy and GPU acceleration auditable and governable.',
    currentReadiness: 'Verified Prototype',
  },
  nextRequiredEvidence: ['Multi-node cluster routing', 'Soak and chaos tests', 'Vendor-specific thermal sensor bridge'],
};
const proofSurfaceRegistry = createDemoProofSurfaceRegistry();
proofSurfaceRegistry.publish(sovereignxRouterProofSurface);

const sovereignxExecutionScaffold = createSovereignXScaffold({
  applicationName: 'ops-console-sovereignx',
});
sovereignxExecutionScaffold.initialize();
sovereignxExecutionScaffold.waitIdle();
sovereignxExecutionScaffold.shutdown();

const sovereignxExecutionProofSurfaces = sovereignxExecutionScaffold
  .listProofSurfaces()
  .filter((surface): surface is SovereignXExecutionProofSurface => surface.kind === 'execution');

for (const executionSurface of sovereignxExecutionProofSurfaces) {
  proofSurfaceRegistry.publish(mapSovereignXExecutionSurface(executionSurface));
}

function loadConstitutionalReleaseReceipt(): ConstitutionalReleaseReceipt | null {
  if (!existsSync(releaseReceiptPath)) {
    return null;
  }
  try {
    return JSON.parse(readFileSync(releaseReceiptPath, 'utf8')) as ConstitutionalReleaseReceipt;
  } catch {
    return null;
  }
}

function mapSovereignXExecutionSurface(surface: SovereignXExecutionProofSurface): ProofSurface {
  const evidenceById = new Map(
    surface.evidenceIds.map((evidenceId, index) => [
      evidenceId,
      {
        id: evidenceId,
        statement: index === 0
          ? `Execution receipt ${evidenceId} proves ${surface.executionContract.operation}.`
          : `Routed evidence ${evidenceId} supports ${surface.executionContract.operation}.`,
        proofLevel: surface.proofLevel,
        verificationStatus: surface.verificationStatus,
        replayable: true,
        verifiedBy: 'packages/sovereignx-router/src/scaffold.ts',
      },
    ] as const),
  );

  return {
    identity: {
      id: `@aaes-os/${surface.id}`,
      name: `SovereignX Execution: ${surface.executionContract.operation}`,
      type: 'runtime',
      version: surface.sourceId,
    },
    purpose: `Expose governed SovereignX execution evidence for ${surface.executionContract.operation}.`,
    claims: [
      {
        id: `${surface.id}-claim`,
        type: 'Verification',
        statement: surface.executionContract.evidence.summary,
        evidenceIds: [...evidenceById.keys()],
        proofLevel: surface.proofLevel,
        verificationStatus: surface.verificationStatus,
        replayStatus: surface.replayStatus,
        operationalStatus: surface.operationalStatus,
      },
    ],
    evidence: [...evidenceById.values()],
    verificationStatus: surface.verificationStatus,
    proofLevel: surface.proofLevel,
    replayStatus: surface.replayStatus,
    operationalStatus: surface.operationalStatus,
    truthBoundary: surface.executionContract.truthBoundary,
    constitutionalProfile: {
      purpose: `Governed execution evidence for ${surface.executionContract.operation}.`,
      authority: surface.executionContract.authority,
      evidenceModel: surface.executionContract.evidence.artifacts.join(', '),
      verificationProcess: surface.executionContract.verification.method,
      complianceRequirements: surface.executionContract.compliance.requirements,
      truthBoundary: surface.executionContract.truthBoundary,
      constitutionalScope: 'SovereignX execution receipts, replayable evidence, and operator-visible proof surfaces.',
      constitutionalLimits: 'Does not claim full cluster orchestration or external GPU hardware validation.',
      dependencies: ['@aaes-os/sovereignx-router'],
      stewardship: 'SovereignX maintainers and ops-console operators',
      replayPath: surface.executionContract.verification.method,
      failurePath: 'Reject execution surfaces without receipts, route evidence, or compliance.',
      currentMaturity: surface.operationalStatus,
    },
    blindspots: [
      'Execution surfaces are demo-generated from the local SovereignX scaffold.',
      'No external GPU hardware telemetry is captured here yet.',
    ],
    battleScars: [
      'Execution evidence used to live only inside generic receipts.',
      'Operator views needed a first-class execution catalog entry.',
    ],
    adversarialClaims: [
      'A receipt can be mistaken for proof without the execution proof surface.',
      'A routed execution can be mistaken for full GPU orchestration.',
    ],
    colorTeamReadiness: {
      redTeam: 'Execution evidence is visible and should be scrutinized for bypass paths.',
      blueTeam: 'Receipts and route evidence remain machine-readable.',
      purpleTeam: 'Execution claims and governance claims can be reconciled in the same catalog.',
      greenTeam: 'Demo generation is deterministic within the local scaffold.',
      yellowTeam: 'Truth boundaries are explicit for operator review.',
      whiteTeam: 'Authority remains separated from presentation.',
    },
    commercialReadiness: {
      targetTier: 'Builder',
      intendedCustomer: 'Operators and governance teams',
      primaryUseCase: 'Execution-proof visibility alongside governance proof surfaces',
      valueProposition: 'A single catalog for receipt-backed execution and governance evidence.',
      currentReadiness: 'Verified Prototype',
    },
    nextRequiredEvidence: [
      'Live GPU-backed execution path',
      'External replay consumer',
      'Operator drill against catalog-published execution receipts',
    ],
  };
}

function buildEvidenceGraph(): ConstitutionalEvidenceGraph {
  const receipt = loadConstitutionalReleaseReceipt();
  const surfaces = proofSurfaceRegistry.list();

  if (receipt) {
    return resolveConstitutionalEvidenceGraphFromReleaseReceipt(receipt, surfaces, {
      source: 'release-receipt',
    });
  }

  return createConstitutionalEvidenceGraphFromProofSurfaces(surfaces, {
    source: 'local-registry',
  });
}

function buildSovereignXHardwareSnapshot(): SovereignXHardwareSnapshot {
  const previousState = sovereignXHardwareGovernor.getState();
  const thermalBridge = sovereignXThermalBridge.snapshot();
  const telemetrySnapshot = sovereignXHardwareTelemetryAdapter.snapshot();
  const cycle = sovereignXHardwareGovernor.step(telemetrySnapshot.telemetry);

  return {
    source: telemetrySnapshot.source,
    sourceDetail: telemetrySnapshot.sourceDetail,
    telemetry: telemetrySnapshot.telemetry,
    cycle,
    thermalBridge,
    governor: {
      contract: sovereignXHardwareGovernor.getContract(),
      invariants: sovereignXHardwareGovernor.getInvariants(),
      previousState,
      state: sovereignXHardwareGovernor.getState(),
      recentEvents: sovereignXHardwareGovernor.listEvents().slice(-5),
    },
  };
}

function captureSovereignXHardwareSnapshot(): SovereignXHardwareSnapshot {
  const snapshot = buildSovereignXHardwareSnapshot();
  sovereignXHardwareReplayStore.append(snapshot);
  return snapshot;
}

function buildSovereignXHardwareOverrideDrill(snapshot: SovereignXHardwareSnapshot) {
  return runSovereignXHardwareOverrideDrill(snapshot, {
    requestedDecision: snapshot.cycle.decision,
    reason: 'operator drill preview',
    authority: 'SovereignX.Router',
  });
}

function buildSovereignXHardwareReplayValidationSummary() {
  const storeSummary = sovereignXHardwareReplayStore.summary();
  return validateSovereignXHardwareReplayRecords(sovereignXHardwareReplayStore.list(), storeSummary.storePath);
}

function buildHardwareConsoleDashboard(): HardwareConsoleSummary {
  const snapshot = buildSovereignXHardwareSnapshot();
  const cluster = buildSovereignXClusterGovernanceSnapshot(snapshot);
  const records = hardwareEvidenceStore.list();
  const benchmarkRuns = records
    .filter((record) => record.kind === 'benchmark')
    .map((record) => record.payload as HardwareBenchmarkRunArtifact);
  const replayArtifacts = records
    .filter((record) => record.kind === 'replay')
    .map((record) => record.payload as HardwareReplayArtifact);

  return buildHardwareConsoleSummary({
    snapshot,
    clusterRouting: cluster.clusterRouting,
    benchmarkRuns,
    replayArtifacts,
  });
}

function createSovereignXClusterRoutingRouter(): SovereignXRouter {
  const router = new SovereignXRouter({ clock: () => Date.now() });
  router.registerIntent({
    id: 'ops-cluster-llm',
    domain: 'llm_step',
    rules: 'cluster routed llm work may use CPU or GPU when governed',
    allowedTargets: ['CPU', 'GPU'],
    maxTokensPerAgentPerMin: 512,
    maxFlopsPerAgentPerMin: 500_000_000_000,
  });
  return router;
}

function buildSovereignXClusterNodes(snapshot: SovereignXHardwareSnapshot): SovereignXClusterNode[] {
  const observedAtMs = snapshot.telemetry.observedAtMs ?? snapshot.governor.state.lastUpdatedAtMs;
  return [
    {
      nodeId: 'cluster-cpu-a',
      role: 'CPU',
      region: 'us-east-1',
      maxJobs: 8,
      activeJobs: 2,
      cpuUtilization: 0.44,
      gpuUtilization: 0.1,
      gpuTempC: Math.min(80, snapshot.telemetry.gpuTempC - 2),
      lastHeartbeatAtMs: observedAtMs - 600,
      health: 'healthy',
    },
    {
      nodeId: 'cluster-gpu-a',
      role: 'GPU',
      region: 'us-east-1',
      maxJobs: 4,
      activeJobs: 1,
      cpuUtilization: 0.2,
      gpuUtilization: snapshot.telemetry.utilization,
      gpuTempC: snapshot.telemetry.gpuTempC,
      lastHeartbeatAtMs: observedAtMs - 350,
      health: snapshot.cycle.decision === 'QUARANTINE' ? 'degraded' : 'healthy',
      preferredBackend: 'opencl',
    },
    {
      nodeId: 'cluster-mixed-a',
      role: 'MIXED',
      region: 'us-west-2',
      maxJobs: 6,
      activeJobs: 0,
      cpuUtilization: 0.17,
      gpuUtilization: 0.22,
      gpuTempC: Math.max(0, snapshot.telemetry.gpuTempC - 4),
      lastHeartbeatAtMs: observedAtMs - 180,
      health: 'healthy',
      preferredBackend: 'vulkan',
    },
  ];
}

type SovereignXClusterRoutingSnapshot = ReturnType<typeof routeSovereignXClusterWork>;

function buildSovereignXClusterRoutingRequest(
  snapshot: SovereignXHardwareSnapshot,
  hardwareEvidence?: SovereignXClusterRouteRequest['hardwareEvidence'],
): SovereignXClusterRouteRequest {
  return {
    workItem: {
      id: `cluster-route-${snapshot.governor.state.lastUpdatedAtMs}`,
      agentId: 'ops-console',
      kind: 'llm_step',
      intentId: 'ops-cluster-llm',
      costEstimateTokens: 144,
      costEstimateFlops: 180_000_000_000,
      priority: 4,
      tenantId: 'SovereignX.Cluster',
    },
    runtime: {
      activeGpuJobs: 1,
      activeCpuJobs: 3,
      gpuUtil: snapshot.telemetry.utilization,
      cpuUtil: 0.32,
      gpuTempC: snapshot.telemetry.gpuTempC,
      vramUsedBytes: 2_000_000_000,
      vramTotalBytes: 16_000_000_000,
    },
    limits: {
      maxGpuJobs: 2,
      maxCpuJobs: 8,
      maxConcurrentJobs: 4,
      maxGpuTempC: 80,
      maxVramBytes: 8_000_000_000,
      maxTokensPerAgentPerMin: 1_000,
      maxFlopsPerAgentPerMin: 1_000_000_000_000,
    },
    nodes: buildSovereignXClusterNodes(snapshot),
    preferredGpuBackend: 'opencl',
    hardwareEvidence,
  };
}

function buildSovereignXClusterGovernanceSnapshot(snapshot: SovereignXHardwareSnapshot) {
  const router = createSovereignXClusterRoutingRouter();
  const request = buildSovereignXClusterRoutingRequest(snapshot, buildHardwareEvidenceContext());
  const clusterRouting = routeSovereignXClusterWork(router, request, {
    clock: () => snapshot.governor.state.lastUpdatedAtMs,
    maxHeartbeatAgeMs: 60_000,
  });
  const clusterGovernance = buildSovereignXClusterGovernanceProjection(
    router,
    request,
    clusterRouting,
    snapshot,
    getSovereignXClusterControlState(),
  );
  return {
    router,
    request,
    clusterRouting,
    clusterGovernance,
  };
}

function buildHardwareEvidenceContext(): SovereignXClusterRouteRequest['hardwareEvidence'] {
  const summary = hardwareEvidenceStore.summary();
  const latestBenchmark = summary.latestBenchmark?.payload as HardwareBenchmarkRunArtifact | undefined;
  const latestReplay = summary.latestReplay?.payload as HardwareReplayArtifact | null;

  const benchmarkArtifactIds = summary.latestBenchmark ? [summary.latestBenchmark.id] : [];
  const replayArtifactIds = summary.latestReplay ? [summary.latestReplay.id] : [];
  const preferredRoute = latestBenchmark ? resolvePreferredHardwareRouteFromBenchmark(latestBenchmark) : undefined;
  const confidence = latestBenchmark ? resolveHardwareEvidenceConfidence(latestBenchmark, latestReplay) : undefined;

  if (benchmarkArtifactIds.length === 0 && replayArtifactIds.length === 0) {
    return undefined;
  }

  return {
    benchmarkArtifactIds,
    replayArtifactIds,
    preferredRoute,
    confidence,
  };
}

function resolvePreferredHardwareRouteFromBenchmark(
  benchmark: HardwareBenchmarkRunArtifact,
): 'cpu' | 'gpu' | 'mixed' | undefined {
  const ranking = benchmark.metrics.throughputPerSec - benchmark.metrics.errorRatePct;
  if (benchmark.route === 'mixed') {
    return 'mixed';
  }
  if (benchmark.route === 'gpu' && ranking >= 0) {
    return 'gpu';
  }
  return benchmark.route;
}

function resolveHardwareEvidenceConfidence(
  benchmark: HardwareBenchmarkRunArtifact,
  replay: HardwareReplayArtifact | null,
): number {
  const base = clamp(benchmark.metrics.thermalHeadroomPct / 100, 0, 1);
  const replayFactor = replay ? clamp(replay.comparison.delta.throughputPerSec >= 0 ? 1 : 0.7, 0, 1) : 0.8;
  return roundTo(base * 0.6 + replayFactor * 0.4, 3);
}

function buildSovereignXHardwareBenchmarks(snapshot: SovereignXHardwareSnapshot): SovereignXHardwareBenchmarks {
  const clusterSnapshot = buildSovereignXClusterGovernanceSnapshot(snapshot);
  const nodes = clusterSnapshot.request.nodes;
  const baselineNode = pickBestHardwareBenchmarkNode(nodes, 'CPU') ?? nodes[0] ?? null;
  const governedNode = clusterSnapshot.clusterRouting.selectedNode ?? pickBestHardwareBenchmarkNode(nodes, 'MIXED') ?? baselineNode;
  const cpuScenario = buildSovereignXHardwareBenchmarkScenario(snapshot, baselineNode, 'cpu-baseline', 'CPU-only baseline', 'cpu');
  const governedScenario = buildSovereignXHardwareBenchmarkScenario(
    snapshot,
    governedNode,
    'governed-route',
    clusterSnapshot.clusterRouting.clusterDecision.action === 'dispatch'
      ? `Governed ${clusterSnapshot.clusterRouting.clusterDecision.backend} dispatch`
      : `Governed ${clusterSnapshot.clusterRouting.clusterDecision.action}`,
    clusterSnapshot.clusterRouting.clusterDecision.backend,
  );
  const gpuScenario = buildSovereignXHardwareBenchmarkScenario(
    snapshot,
    pickBestHardwareBenchmarkNode(nodes, 'GPU'),
    'gpu-counterfactual',
    'GPU counterfactual',
    'opencl',
  );
  const mixedScenario = buildSovereignXHardwareBenchmarkScenario(
    snapshot,
    pickBestHardwareBenchmarkNode(nodes, 'MIXED'),
    'mixed-counterfactual',
    'Mixed-node counterfactual',
    'vulkan',
  );
  const counterfactualScenarios = [gpuScenario, mixedScenario].filter(
    (scenario) => scenario.nodeId !== governedScenario.nodeId || scenario.backend !== governedScenario.backend,
  );
  const comparisons = buildHardwareBenchmarkComparisons(cpuScenario, governedScenario);
  const latencyReductionPct = percentageGain(cpuScenario.estimatedLatencyMs, governedScenario.estimatedLatencyMs, true);
  const throughputGainPct = percentageGain(
    cpuScenario.estimatedThroughputOpsPerSec,
    governedScenario.estimatedThroughputOpsPerSec,
  );
  const costEfficiencyGainPct = percentageGain(
    cpuScenario.estimatedThroughputOpsPerSec / Math.max(0.001, cpuScenario.estimatedCostIndex),
    governedScenario.estimatedThroughputOpsPerSec / Math.max(0.001, governedScenario.estimatedCostIndex),
  );
  const thermalHeadroomDeltaC = Number((governedScenario.estimatedThermalHeadroomC - cpuScenario.estimatedThermalHeadroomC).toFixed(1));
  const recommendation =
    governedScenario.estimatedThroughputOpsPerSec >= cpuScenario.estimatedThroughputOpsPerSec
      ? `Use ${governedScenario.label}; it is estimated to reduce latency by ${latencyReductionPct.toFixed(1)}% and improve throughput by ${throughputGainPct.toFixed(1)}% over CPU-only routing.`
      : `Keep the CPU fallback for this profile; governed routing is not estimated to outperform the CPU baseline under the current thermal profile.`;

  return {
    available: true,
    generatedAtMs: snapshot.telemetry.observedAtMs ?? snapshot.governor.state.lastUpdatedAtMs,
    source: snapshot.source,
    sourceDetail: snapshot.sourceDetail,
    currentDecision: snapshot.cycle.decision,
    baselineScenario: cpuScenario,
    governedScenario,
    counterfactualScenarios,
    comparisons,
    summary: {
      estimatedLatencyReductionPct: latencyReductionPct,
      estimatedThroughputGainPct: throughputGainPct,
      estimatedCostEfficiencyGainPct: costEfficiencyGainPct,
      thermalHeadroomDeltaC,
      recommendation,
    },
  };
}

function pickBestHardwareBenchmarkNode(
  nodes: SovereignXClusterNode[],
  role: SovereignXClusterNode['role'],
): SovereignXClusterNode | null {
  const candidates = nodes.filter((node) => node.role === role || node.role === 'MIXED');
  if (candidates.length === 0) {
    return null;
  }

  return candidates
    .slice()
    .sort((left, right) =>
      left.health.localeCompare(right.health) ||
      left.activeJobs - right.activeJobs ||
      left.gpuTempC - right.gpuTempC ||
      left.nodeId.localeCompare(right.nodeId),
    )[0] ?? null;
}

function buildSovereignXHardwareBenchmarkScenario(
  snapshot: SovereignXHardwareSnapshot,
  node: SovereignXClusterNode | null,
  scenarioId: string,
  label: string,
  backend: string,
): SovereignXHardwareBenchmarkScenario {
  const utilization = clamp(snapshot.telemetry.utilization, 0, 1);
  const cpuTemp = snapshot.telemetry.cpuTempC;
  const gpuTemp = snapshot.telemetry.gpuTempC;
  const power = clamp(snapshot.telemetry.powerDrawFraction, 0, 1);
  const nodeLoad = node ? clamp(node.activeJobs / Math.max(1, node.maxJobs), 0, 1) : 1;
  const role = node?.role ?? null;
  const temperature = role === 'GPU' ? gpuTemp : cpuTemp;
  const thermalPressure = clamp((temperature - 55) / 35, 0, 1);
  const roleBias = role === 'GPU' ? 0.84 : role === 'MIXED' ? 0.92 : 1;
  const latencyMs = roundTo(860 * (0.46 + utilization * 0.34 + nodeLoad * 0.19 + thermalPressure * 0.11) * roleBias, 1);
  const throughputOpsPerSec = roundTo(1000 / Math.max(1, latencyMs), 3);
  const costIndex = roundTo((role === 'GPU' ? 1.22 : role === 'MIXED' ? 1.08 : 1.0) * (1 + nodeLoad * 0.08 + power * 0.05), 3);
  const estimatedThermalHeadroomC = roundTo(Math.max(0, 95 - temperature - (role === 'GPU' ? 2.5 : 0)), 1);
  const estimatedThrottleRisk = roundTo(clamp((power * 0.35 + thermalPressure * 0.45 + nodeLoad * 0.2 + (snapshot.cycle.decision === 'QUARANTINE' ? 0.2 : 0)), 0, 1), 3);

  return {
    scenarioId,
    label,
    backend,
    nodeId: node?.nodeId ?? null,
    nodeRole: role,
    estimatedLatencyMs: latencyMs,
    estimatedThroughputOpsPerSec: throughputOpsPerSec,
    estimatedCostIndex: costIndex,
    estimatedThermalHeadroomC,
    estimatedThrottleRisk,
    notes: buildHardwareBenchmarkNotes(snapshot, node, role, backend),
  };
}

function buildHardwareBenchmarkNotes(
  snapshot: SovereignXHardwareSnapshot,
  node: SovereignXClusterNode | null,
  role: SovereignXClusterNode['role'] | null,
  backend: string,
): string[] {
  const notes = [
    `Telemetry source: ${snapshot.source} (${snapshot.sourceDetail})`,
    `Governor decision: ${snapshot.cycle.decision}`,
    `Estimated backend: ${backend}`,
  ];

  if (!node) {
    notes.push('No eligible node was available for this counterfactual.');
    return notes;
  }

  notes.push(`Selected node ${node.nodeId} (${role ?? 'unknown'}) at ${Math.round(node.activeJobs / Math.max(1, node.maxJobs) * 100)}% active capacity.`);
  if (snapshot.cycle.decision === 'QUARANTINE') {
    notes.push('Thermal pressure is high enough that the governor is in quarantine mode, so benchmark gains should be treated conservatively.');
  }

  return notes;
}

function buildHardwareBenchmarkComparisons(
  baseline: SovereignXHardwareBenchmarkScenario,
  governed: SovereignXHardwareBenchmarkScenario,
): SovereignXHardwareBenchmarkComparison[] {
  return [
    comparisonRow('Latency (ms)', baseline.estimatedLatencyMs, governed.estimatedLatencyMs, true),
    comparisonRow('Throughput (ops/s)', baseline.estimatedThroughputOpsPerSec, governed.estimatedThroughputOpsPerSec, false),
    comparisonRow('Cost index', baseline.estimatedCostIndex, governed.estimatedCostIndex, true),
    comparisonRow('Thermal headroom (°C)', baseline.estimatedThermalHeadroomC, governed.estimatedThermalHeadroomC, false),
    comparisonRow('Throttle risk', baseline.estimatedThrottleRisk, governed.estimatedThrottleRisk, true),
  ];
}

function comparisonRow(metric: string, baseline: number, governed: number, lowerIsBetter: boolean): SovereignXHardwareBenchmarkComparison {
  const delta = roundTo(governed - baseline, 3);
  const deltaPct = lowerIsBetter
    ? percentageGain(baseline, governed, true)
    : percentageGain(baseline, governed, false);

  return {
    metric,
    baseline,
    governed,
    delta,
    deltaPct,
  };
}

function percentageGain(baseline: number, governed: number, lowerIsBetter = false): number {
  if (baseline === 0) {
    return 0;
  }

  const raw = lowerIsBetter
    ? ((baseline - governed) / baseline) * 100
    : ((governed - baseline) / baseline) * 100;
  return roundTo(raw, 2);
}

function buildSovereignXHardwareProofSurface(snapshot: SovereignXHardwareSnapshot): ProofSurface {
  const runtimeEvidenceId = 'ops-router-evidence-hardware-governor';
  const replayStoreSummary = sovereignXHardwareReplayStore.summary();
  const thermalBridge = snapshot.thermalBridge;
  return {
    identity: {
      id: '@aaes-os/sovereignx-hardware-runtime-governor',
      name: 'SovereignX Hardware Runtime Governor',
      type: 'runtime',
      version: snapshot.governor.state.lastUpdatedAtMs.toString(),
    },
    purpose: 'Expose a live hardware telemetry snapshot as a constitutional runtime proof surface.',
    claims: [
      {
        id: 'ops-hardware-governor-telemetry-valid',
        type: 'Verification',
        statement: 'The live hardware telemetry snapshot is validated before the governor publishes a constitutional decision.',
        evidenceIds: [runtimeEvidenceId],
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
      {
        id: 'ops-hardware-governor-first-class-runtime',
        type: 'Architectural',
        statement: 'The SovereignX hardware governor is surfaced as a first-class runtime catalog entry, not just an API payload.',
        evidenceIds: [runtimeEvidenceId, 'ops-router-evidence-tests'],
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
      {
        id: 'ops-hardware-governor-replay-store',
        type: 'Architectural',
        statement: 'The live hardware snapshot is durably appended to the persistent replay store so operators can inspect the decision trail.',
        evidenceIds: [runtimeEvidenceId],
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
      {
        id: 'ops-hardware-governor-thermal-bridge',
        type: 'Architectural',
        statement: thermalBridge
          ? `Vendor-specific thermal sensors from ${thermalBridge.vendor} ${thermalBridge.healthy ? 'feed' : 'stress'} the bridge with ${thermalBridge.summary.alertCount} alerting sensor${thermalBridge.summary.alertCount === 1 ? '' : 's'}.`
          : 'Vendor-specific thermal sensors feed the hardware bridge and are surfaced as first-class operator evidence.',
        evidenceIds: ['ops-router-evidence-thermal-bridge'],
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
      {
        id: 'ops-hardware-governor-override-drill',
        type: 'Verification',
        statement: 'An operator override drill can preview governor state without mutating the live hardware governor.',
        evidenceIds: ['ops-router-evidence-override-drill'],
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
      {
        id: 'ops-hardware-governor-replay-validation',
        type: 'Verification',
        statement: 'Replay and chaos validation exercises stored hardware decisions against fresh governors and perturbation cases.',
        evidenceIds: ['ops-router-evidence-replay-validation'],
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
    ],
    evidence: [
      {
        id: runtimeEvidenceId,
        statement: `Live telemetry from ${snapshot.source} source ${snapshot.sourceDetail} produced a ${snapshot.cycle.decision} decision.`,
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'services/ops-console/src/server.ts',
        timestamp: new Date(snapshot.telemetry.observedAtMs ?? snapshot.governor.state.lastUpdatedAtMs).toISOString(),
      },
      {
        id: 'ops-router-evidence-hardware-replay-store',
        statement: `Hardware replay store ${replayStoreSummary.available ? 'contains' : 'exposes'} ${replayStoreSummary.entryCount} recorded snapshot${replayStoreSummary.entryCount === 1 ? '' : 's'} at ${replayStoreSummary.storePath}.`,
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'services/ops-console/src/sovereignxHardwareReplayStore.ts',
      },
      {
        id: 'ops-router-evidence-thermal-bridge',
        statement: thermalBridge
          ? `Thermal bridge snapshot from ${thermalBridge.vendor} on ${thermalBridge.deviceFamily} reported ${thermalBridge.summary.hottestSensor} at ${thermalBridge.summary.hottestTemperatureC} °C.`
          : 'Thermal bridge snapshot is generated from the vendor-specific adapter and summarized for operators.',
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'services/ops-console/src/sovereignxHardwareThermalBridge.ts',
      },
      {
        id: 'ops-router-evidence-override-drill',
        statement: 'Operator override drills are audit-only previews that report accepted or rejected override requests against the live governor state.',
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'services/ops-console/src/sovereignxHardwareOverrideDrill.ts',
      },
      {
        id: 'ops-router-evidence-replay-validation',
        statement: 'Replay validation replays stored hardware decisions and injects thermal, voltage, and utilization chaos cases against fresh governors.',
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayable: true,
        verifiedBy: 'services/ops-console/src/sovereignxHardwareReplayValidation.ts',
      },
      {
        id: 'ops-router-evidence-tests',
        statement: 'Ops-console tests verify the hardware governor telemetry adapter, routed snapshot, replay store, thermal bridge, override drill, replay validation, and dedicated hardware route.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'services/ops-console/src/server.test.ts',
      },
    ],
    verificationStatus: 'Implemented',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'This runtime entry proves a live governed snapshot plus vendor thermal bridge, override drill, and replay validation, not direct firmware control.',
    constitutionalProfile: {
      purpose: 'Expose live hardware telemetry as a first-class runtime proof surface.',
      authority: 'AAES governance law, proof-surface law, and the SovereignX hardware governor contract.',
      evidenceModel: 'Live telemetry snapshots, replayable governor transitions, and ops-console tests.',
      verificationProcess: 'Fetch the live snapshot, validate the governor output, and inspect replayable events.',
      complianceRequirements: [
        'Telemetry must be validated before governor decisions are published',
        'Runtime proof surface must stay replayable',
        'No claim may exceed the measured snapshot',
      ],
      truthBoundary: 'This proof surface exposes a live runtime snapshot and its decision trail, not direct hardware control.',
      constitutionalScope: 'Hardware telemetry ingestion, constitutional validation, and governed promotion/retraction.',
      constitutionalLimits: 'It does not claim direct firmware control, mutating overrides, or production chaos automation.',
      dependencies: ['@aaes-os/sovereignx-router'],
      stewardship: 'SovereignX maintainers and ops-console operators',
      replayPath: 'Replay the hardware telemetry snapshot, durable JSONL store, vendor bridge, and governor transition history.',
      failurePath: 'Quarantine or retract when telemetry breaches the invariant contract.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: [
      'Telemetry remains adapter-backed rather than firmware-native control.',
      'The runtime surface reflects a point-in-time snapshot on request.',
      'Replay history validates deterministic execution, not live production chaos.',
    ],
    battleScars: [
      'Live telemetry is easy to hide behind a generic API payload.',
      'Hardware state needs a catalog entry to be operator-visible.',
      'Replay history needed a durable JSONL store before operators could inspect the sequence.',
      'Vendor sensor bridges can be mistaken for direct hardware control if the boundary is not stated.',
    ],
    adversarialClaims: [
      'A generated snapshot could be mistaken for a direct hardware sensor feed.',
      'A valid runtime entry could be mistaken for firmware control.',
    ],
    colorTeamReadiness: {
      redTeam: 'Snapshot data must be assumed inspectable, spoofable, and stale until proven otherwise.',
      blueTeam: 'The adapter and governor both emit replayable state for inspection.',
      purpleTeam: 'The same snapshot powers telemetry, routing, and proof-surface visibility.',
      greenTeam: 'The implementation is deterministic enough for local verification.',
      yellowTeam: 'The source is clearly labeled as adapter-backed rather than vendor-native.',
      whiteTeam: 'Authority remains separated from runtime presentation.',
    },
    commercialReadiness: {
      targetTier: 'Builder',
      intendedCustomer: 'Operators building governed runtime consoles',
      primaryUseCase: 'Hardware telemetry visibility with constitutional decisioning',
      valueProposition: 'Turns live hardware state into a cataloged proof surface with replayable evidence.',
      currentReadiness: 'Prototype',
    },
    nextRequiredEvidence: [
      'External orchestrator integration',
      'Cloud failover execution path',
      'Control-plane persistence',
    ],
  };
}

function buildSovereignXClusterRoutingProofSurface(
  clusterRouting: SovereignXClusterRoutingSnapshot,
): ProofSurface {
  const selectedNode = clusterRouting.selectedNode;
  return {
    identity: {
      id: '@aaes-os/sovereignx-cluster-routing-runtime',
      name: 'SovereignX Cluster Routing Runtime',
      type: 'runtime',
      version: clusterRouting.routeEvaluation.evidence.timestamp,
    },
    purpose: 'Expose deterministic multi-node work assignment as a constitutional runtime proof surface.',
    claims: [
      {
        id: 'ops-cluster-routing-deterministic-assignment',
        type: 'Architectural',
        statement: 'The cluster router deterministically assigns governed work to the best eligible node after the local CPU or GPU routing decision.',
        evidenceIds: ['ops-router-evidence-cluster-routing'],
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
      {
        id: 'ops-cluster-routing-fallback',
        type: 'Verification',
        statement: 'The runtime proof surface records delay behavior when no eligible node is available for the governed work item.',
        evidenceIds: ['ops-router-evidence-cluster-routing', 'ops-router-evidence-tests'],
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
    ],
    evidence: [
      {
        id: 'ops-router-evidence-cluster-routing',
        statement: selectedNode
          ? `Cluster routing assigned ${clusterRouting.clusterDecision.nodeId} in ${selectedNode.region} using ${clusterRouting.clusterDecision.backend} with ${clusterRouting.summary.eligibleNodeCount} eligible nodes.`
          : `Cluster routing deferred with ${clusterRouting.summary.eligibleNodeCount} eligible nodes and action ${clusterRouting.clusterDecision.action}.`,
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'services/ops-console/src/server.ts',
        timestamp: clusterRouting.routeEvaluation.evidence.timestamp,
      },
      {
        id: 'ops-router-evidence-tests',
        statement: 'Ops-console tests verify the cluster routing endpoint, selected node, and fallback behavior across multiple nodes.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'services/ops-console/src/server.test.ts',
      },
    ],
    verificationStatus: 'Implemented',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'This runtime entry proves deterministic multi-node assignment, not live cluster membership control or autoscaling.',
    constitutionalProfile: {
      purpose: 'Expose governed multi-node routing alongside the local CPU and GPU decision.',
      authority: 'AAES governance law, proof-surface law, and the SovereignX router cluster policy.',
      evidenceModel: 'Cluster node scores, selected node assignments, delay fallbacks, and tests.',
      verificationProcess: 'Inspect the selected node, replay the node scores, and validate the delayed fallback path.',
      complianceRequirements: [
        'No claim may exceed the eligible node set',
        'The cluster must obey the local CPU or GPU governance decision',
        'Fallback must be visible when no node is eligible',
      ],
      truthBoundary: 'This proof surface exposes deterministic cluster placement, not live cluster membership control.',
      constitutionalScope: 'Deterministic multi-node assignment, node scoring, and fallback routing.',
      constitutionalLimits: 'It does not claim autoscaling, cluster membership, or distributed consensus control.',
      dependencies: ['@aaes-os/sovereignx-router'],
      stewardship: 'SovereignX maintainers and ops-console operators',
      replayPath: 'Replay the selected node, the node scores, and the deterministic fallback path.',
      failurePath: 'Delay when no eligible node can host the governed work item.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: [
      'The demo cluster topology is still static.',
      'Membership and autoscaling are outside this slice.',
      'Placement is deterministic, not a live scheduler integration.',
    ],
    battleScars: [
      'Cluster routing can look like scheduling if the selected node is not named explicitly.',
      'Fallback paths need to be visible so delays do not appear as silent failures.',
    ],
    adversarialClaims: [
      'A node assignment can be mistaken for autoscaling.',
      'A deterministic placement can be mistaken for distributed consensus.',
    ],
    colorTeamReadiness: {
      redTeam: 'Node selection must be assumed inspectable and replayable.',
      blueTeam: 'Eligible nodes and fallback paths are visible in the console.',
      purpleTeam: 'The local router decision and the cluster placement can be reasoned about together.',
      greenTeam: 'Selection stays deterministic under a fixed topology.',
      yellowTeam: 'The cluster remains a demo topology, not a production scheduler.',
      whiteTeam: 'Authority remains separated from placement.',
    },
    commercialReadiness: {
      targetTier: 'Builder',
      intendedCustomer: 'Operators building governed multi-node compute runtimes',
      primaryUseCase: 'Deterministic multi-node placement under CPU and GPU governance',
      valueProposition: 'Turns placement policy into a visible, replayable runtime entry.',
      currentReadiness: 'Prototype',
    },
    nextRequiredEvidence: [
      'External scheduler integration',
      'Consensus-backed topology inventory',
      'Cloud placement control',
    ],
  };
}

function buildSovereignXClusterGovernanceProofSurface(
  clusterGovernanceSnapshot: SovereignXClusterGovernanceProjection,
  clusterRouting: SovereignXClusterRoutingSnapshot,
): ProofSurface {
  return {
    identity: {
      id: '@aaes-os/sovereignx-cluster-governance-runtime',
      name: 'SovereignX Cluster Governance Runtime',
      type: 'runtime',
      version: clusterRouting.routeEvaluation.evidence.timestamp,
    },
    purpose: 'Expose live cluster membership control, autoscaling, and failover as a constitutional runtime proof surface.',
    claims: [
      {
        id: 'ops-cluster-governance-membership-control',
        type: 'Architectural',
        statement: 'The live cluster control plane can quarantine, restore, and project active or standby membership from the current topology.',
        evidenceIds: ['ops-router-evidence-cluster-membership'],
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
      {
        id: 'ops-cluster-governance-autoscaling-failover',
        type: 'Architectural',
        statement: 'Autoscaling and failover integration derive from the current routing and membership pressure instead of a static demo topology.',
        evidenceIds: ['ops-router-evidence-cluster-membership', 'ops-router-evidence-tests'],
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
      {
        id: 'ops-cluster-governance-soak-chaos',
        type: 'Verification',
        statement: 'Soak and chaos validation exercises the cluster control plane across repeated and adverse routing scenarios.',
        evidenceIds: ['ops-router-evidence-cluster-membership', 'ops-router-evidence-tests'],
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
    ],
    evidence: [
      {
        id: 'ops-router-evidence-cluster-membership',
        statement: `Cluster membership projects ${clusterGovernanceSnapshot.summary.activeNodeCount} active nodes, ${clusterGovernanceSnapshot.summary.standbyNodeCount} standby nodes, ${clusterGovernanceSnapshot.summary.quarantinedNodeCount} quarantined nodes, and ${clusterGovernanceSnapshot.autoscaling.action} / ${clusterGovernanceSnapshot.failover.action} control recommendations.`,
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'services/ops-console/src/server.ts',
        timestamp: clusterRouting.routeEvaluation.evidence.timestamp,
      },
      {
        id: 'ops-router-evidence-tests',
        statement: 'Ops-console tests verify live cluster membership control, autoscaling and failover integration, and soak and chaos validation.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'services/ops-console/src/server.test.ts',
      },
    ],
    verificationStatus: 'Implemented',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'This runtime entry proves live membership control and deterministic failover recommendations, not production orchestration or consensus.',
    constitutionalProfile: {
      purpose: 'Expose live cluster membership control and control-plane recommendations.',
      authority: 'AAES governance law, proof-surface law, and the SovereignX cluster control contract.',
      evidenceModel: 'Cluster membership state, autoscaling recommendations, failover planning, and soak or chaos validation.',
      verificationProcess: 'Inspect the membership projection, review the autoscaling and failover recommendations, and replay the soak or chaos validation rows.',
      complianceRequirements: [
        'Membership changes must remain visible',
        'Autoscaling must remain tied to the current topology',
        'Failover must prefer eligible standby nodes',
      ],
      truthBoundary: 'This proof surface exposes live cluster governance, not a production control plane.',
      constitutionalScope: 'Cluster membership, autoscaling, failover, and validation of routing pressure.',
      constitutionalLimits: 'It does not claim distributed consensus, external orchestrator control, or cloud control-plane integration.',
      dependencies: ['@aaes-os/sovereignx-router'],
      stewardship: 'SovereignX maintainers and ops-console operators',
      replayPath: 'Replay the control state, routing snapshot, and soak or chaos validation rows.',
      failurePath: 'Quarantine or scale up when eligible cluster capacity drops below the desired membership.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: [
      'Membership control is still local to the ops-console runtime.',
      'The topology remains a deterministic projection rather than a cloud control plane.',
      'External autoscaler and orchestrator integrations are still future work.',
    ],
    battleScars: [
      'Cluster state can look static when the control projection is not first-class.',
      'Failover logic needs explicit evidence to avoid appearing hand-waved.',
    ],
    adversarialClaims: [
      'A membership projection can be mistaken for a full control plane.',
      'Autoscaling recommendations can be mistaken for automatic cloud orchestration.',
    ],
    colorTeamReadiness: {
      redTeam: 'Membership projections and failover targets must be assumed inspectable.',
      blueTeam: 'Control state is visible and replayable through the ops console.',
      purpleTeam: 'Routing, membership, and validation can be audited together.',
      greenTeam: 'Deterministic control responses are suitable for local verification.',
      yellowTeam: 'This remains a governed demo control plane, not cloud-native orchestration.',
      whiteTeam: 'Authority remains separated from runtime presentation.',
    },
    commercialReadiness: {
      targetTier: 'Builder',
      intendedCustomer: 'Operators building governed cluster runtimes',
      primaryUseCase: 'Visible membership control with autoscaling and failover recommendations',
      valueProposition: 'Turns live cluster governance into a replayable runtime entry.',
      currentReadiness: 'Prototype',
    },
    nextRequiredEvidence: [
      'External orchestrator integration',
      'Cluster control persistence',
      'Cloud failover execution path',
    ],
  };
}

function buildSovereignXTraceabilityProofSurface(
  clusterGovernanceSnapshot: SovereignXClusterGovernanceProjection,
  clusterRouting: SovereignXClusterRoutingSnapshot,
): ProofSurface {
  const matrix = clusterGovernanceSnapshot.traceabilityMatrix;
  return {
    identity: {
      id: '@aaes-os/constitutional-traceability-runtime',
      name: 'Constitutional Traceability Runtime',
      type: 'runtime',
      version: clusterRouting.routeEvaluation.evidence.timestamp,
    },
    purpose: 'Expose a machine-readable traceability matrix that maps runtime capabilities to constitutional requirements, evidence, and tests.',
    claims: [
      {
        id: 'ops-traceability-matrix-linked',
        type: 'Verification',
        statement: 'The traceability matrix maps each major runtime capability to constitutional requirements, architectural components, evidence, and tests.',
        evidenceIds: ['ops-router-evidence-traceability-matrix'],
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
      {
        id: 'ops-traceability-first-class-proof-surface',
        type: 'Architectural',
        statement: 'The traceability matrix is published as a first-class runtime proof surface so it can evolve with the project.',
        evidenceIds: ['ops-router-evidence-traceability-matrix', 'ops-router-evidence-tests'],
        proofLevel: 'P2',
        verificationStatus: 'Implemented',
        replayStatus: 'Replayable',
        operationalStatus: 'Verified Prototype',
      },
    ],
    evidence: [
      {
        id: 'ops-router-evidence-traceability-matrix',
        statement: `Traceability matrix covers ${matrix.summary.capabilityCount} capabilities, ${matrix.summary.requirementCount} constitutional requirement entries, ${matrix.summary.evidenceCount} evidence links, and ${matrix.summary.testCount} tests.`,
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'services/ops-console/src/server.ts',
        timestamp: clusterRouting.routeEvaluation.evidence.timestamp,
      },
      {
        id: 'ops-router-evidence-tests',
        statement: 'Ops-console tests verify the traceability matrix, live cluster governance, and published proof surfaces.',
        proofLevel: 'P2',
        verificationStatus: 'Test Verified',
        replayable: true,
        verifiedBy: 'services/ops-console/src/server.test.ts',
      },
    ],
    verificationStatus: 'Implemented',
    proofLevel: 'P2',
    replayStatus: 'Replayable',
    operationalStatus: 'Verified Prototype',
    truthBoundary: 'This runtime entry proves constitutional traceability and evidence linkage, not constitutional authorship or formal certification.',
    constitutionalProfile: {
      purpose: 'Map runtime capabilities to constitutional requirements, evidence, and tests.',
      authority: 'AAES governance law, proof-surface law, and the operator-visible conformance surface.',
      evidenceModel: 'Traceability rows, proof-surface links, and test identifiers.',
      verificationProcess: 'Inspect the matrix rows, confirm the evidence and test references, and replay the proof-surface catalog.',
      complianceRequirements: [
        'Each major runtime capability must map to constitutional requirements',
        'Each capability must point at an architectural component',
        'Each capability must cite evidence and tests',
      ],
      truthBoundary: 'This proof surface exposes traceability, not the constitutional text itself.',
      constitutionalScope: 'Machine-readable runtime traceability and conformance mapping.',
      constitutionalLimits: 'It does not certify external systems or replace constitutional chapters.',
      dependencies: ['@aaes-os/sovereignx-router'],
      stewardship: 'AAES-OS governance maintainers',
      replayPath: 'Replay the traceability matrix and proof-surface catalog entries.',
      failurePath: 'Reject capabilities that cannot point to explicit evidence and tests.',
      currentMaturity: 'Verified Prototype',
    },
    blindspots: [
      'The matrix is only as complete as the capability inventory that feeds it.',
      'Constitutional chapters still need to be bound to exact chapter identifiers.',
    ],
    battleScars: [
      'Traceability used to live only in prose and comments.',
      'Capability coverage needed an explicit machine-readable surface.',
    ],
    adversarialClaims: [
      'A runtime capability can be mistaken for a constitutional guarantee without the matrix.',
      'A proof-surface entry can be mistaken for full conformance without traceability rows.',
    ],
    colorTeamReadiness: {
      redTeam: 'The matrix must be assumed incomplete until evidence and tests are present.',
      blueTeam: 'Rows are visible and tied to concrete proof-surface entries.',
      purpleTeam: 'Conformance reasoning can span runtime, evidence, and tests.',
      greenTeam: 'The matrix is deterministic and local to the workspace.',
      yellowTeam: 'Conformance is traceable, not yet certified by an external body.',
      whiteTeam: 'Authority remains separated from runtime presentation.',
    },
    commercialReadiness: {
      targetTier: 'Builder',
      intendedCustomer: 'Governance and platform teams',
      primaryUseCase: 'Conformance traceability for runtime capabilities',
      valueProposition: 'Turns runtime features into auditable constitutional rows.',
      currentReadiness: 'Prototype',
    },
    nextRequiredEvidence: [
      'Bound constitutional chapter identifiers',
      'Automated conformance suite execution',
      'External evidence catalog integration',
    ],
  };
}

async function getPlatformApiSessionId(): Promise<string | null> {
  if (!platformApiSessionIdPromise) {
    platformApiSessionIdPromise = fetch(`${platformApiBaseUrl}/v1/auth/login`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        ownerId: 'ops-console',
        governanceProfile: 'balanced',
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          return null;
        }
        const payload = (await response.json().catch(() => ({}))) as { sessionId?: string };
        return payload.sessionId ?? null;
      })
      .catch(() => null);
  }

  return platformApiSessionIdPromise;
}

async function fetchPlatformCustomers() {
  const sessionId = await getPlatformApiSessionId();
  if (!sessionId) {
    return [];
  }

  const response = await fetch(`${platformApiBaseUrl}/v1/customers`, {
    headers: {
      'x-session-id': sessionId,
      accept: 'application/json',
    },
  });
  if (!response.ok) {
    return [];
  }

  const payload = (await response.json().catch(() => ({ customers: [] }))) as {
    customers?: {
      id: string;
      email: string;
      planId: string;
      planName: string;
      entitlements: { routingTier: string; codexPacketHandoff: boolean; usageLedger: boolean; marginDashboard: boolean; auditScope: string };
      createdAt: string;
    }[];
  };
  return payload.customers ?? [];
}

async function fetchPlatformOrganizations() {
  const sessionId = await getPlatformApiSessionId();
  if (!sessionId) {
    return [];
  }

  const response = await fetch(`${platformApiBaseUrl}/v1/organizations`, {
    headers: {
      'x-session-id': sessionId,
      accept: 'application/json',
    },
  });
  if (!response.ok) {
    return [];
  }

  const payload = (await response.json().catch(() => ({ organizations: [] }))) as {
    organizations?: {
      id: string;
      name: string;
      ownerCustomerId: string;
      billingContactEmail: string;
      domain?: string;
      members: { customerId: string; role: string; joinedAt: string }[];
      createdAt: string;
      updatedAt: string;
    }[];
  };
  return payload.organizations ?? [];
}

async function fetchPlatformQuota() {
  const sessionId = await getPlatformApiSessionId();
  if (!sessionId) {
    return null;
  }

  const response = await fetch(`${platformApiBaseUrl}/v1/customers/quota`, {
    headers: {
      'x-session-id': sessionId,
      accept: 'application/json',
    },
  });
  if (!response.ok) {
    return null;
  }

  const payload = (await response.json().catch(() => ({ customer: null, quota: null, usageRecords: [] }))) as {
    customer?: {
      id: string;
      email: string;
      planName: string;
      organizationId?: string;
      organizationRole?: string;
      entitlements: {
        routingTier: string;
        codexPacketHandoff: boolean;
        usageLedger: boolean;
        marginDashboard: boolean;
        auditScope: string;
      };
    };
    quota?: {
      requestLimit: number;
      requestCount: number;
      requestOverage: number;
      tokenLimit: number;
      tokenCount: number;
      tokenOverage: number;
      overageBillingUsd: number;
      overageBillingEnabled: boolean;
      enforcement: {
        status: 'within_limit' | 'metered_overage' | 'blocked';
        allowed: boolean;
        reason: string;
      };
    };
    usageRecords?: { operation: string; units: number; timestamp: string }[];
  };
  return payload.quota
    ? {
        customer: payload.customer,
        quota: payload.quota,
        usageRecords: payload.usageRecords ?? [],
      }
    : null;
}

async function fetchPlatformOrganizationUsage(organizationId: string) {
  const sessionId = await getPlatformApiSessionId();
  if (!sessionId) {
    return null;
  }

  const response = await fetch(`${platformApiBaseUrl}/v1/organizations/${encodeURIComponent(organizationId)}/usage`, {
    headers: {
      'x-session-id': sessionId,
      accept: 'application/json',
    },
  });
  if (!response.ok) {
    return null;
  }

  return (await response.json().catch(() => null)) as
    | {
        organizationId: string;
        total: number;
        byKind: Record<string, number>;
        summary: { total: number; byKind: Record<string, number> };
        overageEvents: { id: string; kind: string; amount: number; occurredAt: string; metadata?: Record<string, unknown> }[];
      }
    | null;
}

async function fetchPlatformOrganizationAudit(organizationId: string) {
  const sessionId = await getPlatformApiSessionId();
  if (!sessionId) {
    return null;
  }

  const [pricingRes, routingRes, entitlementsRes] = await Promise.all([
    fetch(`${platformApiBaseUrl}/v1/organizations/${encodeURIComponent(organizationId)}/audit/pricing`, {
      headers: {
        'x-session-id': sessionId,
        accept: 'application/json',
      },
    }),
    fetch(`${platformApiBaseUrl}/v1/organizations/${encodeURIComponent(organizationId)}/audit/routing`, {
      headers: {
        'x-session-id': sessionId,
        accept: 'application/json',
      },
    }),
    fetch(`${platformApiBaseUrl}/v1/organizations/${encodeURIComponent(organizationId)}/audit/entitlements`, {
      headers: {
        'x-session-id': sessionId,
        accept: 'application/json',
      },
    }),
  ]);

  if (!pricingRes.ok && !routingRes.ok && !entitlementsRes.ok) {
    return null;
  }

  const [pricingBody, routingBody, entitlementsBody] = await Promise.all([
    pricingRes.json().catch(() => ({ audit: [] })),
    routingRes.json().catch(() => ({ audit: [] })),
    entitlementsRes.json().catch(() => ({ audit: [] })),
  ]);

  return {
    pricing: pricingRes.ok ? ((pricingBody as { audit?: unknown[] }).audit ?? []) : [],
    routing: routingRes.ok ? ((routingBody as { audit?: unknown[] }).audit ?? []) : [],
    entitlements: entitlementsRes.ok ? ((entitlementsBody as { audit?: unknown[] }).audit ?? []) : [],
  };
}

async function fetchPlatformTreasurySchedule() {
  const sessionId = await getPlatformApiSessionId();
  if (!sessionId) {
    return null;
  }

  const response = await fetch(`${platformApiBaseUrl}/v1/billing/treasury/schedule`, {
    headers: {
      'x-session-id': sessionId,
      accept: 'application/json',
    },
  });
  if (!response.ok) {
    return null;
  }

  const payload = (await response.json().catch(() => ({ schedule: null }))) as {
    schedule?: {
      scheduledAt: string;
      source: 'ledger';
      customerId: string;
      ownerId: string;
      governanceProfile: string;
      instructions: {
        openAI: { destination: string; channel: string; amountUsd: number; notes: string };
        tax: { destination: string; channel: string; amountUsd: number; notes: string };
        ownerProfit: { destination: string; channel: string; amountUsd: number; notes: string };
      };
      sourcePlan: {
        grossInvoiceUsd: number;
        openAiUsageCostUsd: number;
        taxReserveUsd: number;
        platformReserveUsd: number;
        ownerProfitUsd: number;
        totalReserveUsd: number;
        netAfterReservesUsd: number;
        providers?: unknown;
        remittanceInstructions: unknown;
        providerNotes: {
          customerCollection: string;
          openAI: string;
          tax: string;
          profit: string;
        };
        adapters: {
          paypalCheckout: {
            enabled: boolean;
            environment: string;
            apiBaseUrl: string;
            createOrderPath: string;
            captureOrderPath: string;
            orderRequest: {
              intent: string;
              application_context: {
                brand_name: string;
                landing_page: string;
                user_action: string;
                return_url: string;
                cancel_url: string;
              };
              purchase_units: Array<{
                reference_id: string;
                description: string;
                custom_id: string;
                amount: { currency_code: string; value: string };
              }>;
            };
          };
          paypalPayout: {
            enabled: boolean;
            environment: string;
            apiBaseUrl: string;
            createBatchPath: string;
            batchRequest: {
              sender_batch_header: {
                sender_batch_id: string;
                email_subject: string;
                email_message: string;
              };
              items: Array<{
                recipient_type: string;
                amount: { currency: string; value: string };
                receiver: string;
                note: string;
                sender_item_id: string;
              }>;
            };
          };
        };
      };
    } | null;
  };
  return payload.schedule ?? null;
}

function summarizeOpsConsoleProofSurfaces(records: ProofSurface[]) {
  return listProofSurfaceSummaries({
    list: () => records,
  } as unknown as ReturnType<typeof createDemoProofSurfaceRegistry>);
}

function listOpsConsoleProofSurfaces(snapshot?: SovereignXHardwareSnapshot): ProofSurface[] {
  const hardwareSnapshot = snapshot ?? buildSovereignXHardwareSnapshot();
  const clusterGovernanceSnapshot = buildSovereignXClusterGovernanceSnapshot(hardwareSnapshot);
  return [
    ...proofSurfaceRegistry.list(),
    buildSovereignXHardwareProofSurface(hardwareSnapshot),
    buildSovereignXClusterRoutingProofSurface(clusterGovernanceSnapshot.clusterRouting),
    buildSovereignXClusterGovernanceProofSurface(clusterGovernanceSnapshot.clusterGovernance, clusterGovernanceSnapshot.clusterRouting),
    buildSovereignXTraceabilityProofSurface(clusterGovernanceSnapshot.clusterGovernance, clusterGovernanceSnapshot.clusterRouting),
  ];
}

type CepViewState = {
  selectedKind: CepArtifactKind;
  selectedArtifactId: string | null;
  updatedAt: string;
  source: 'local' | 'remote';
};

function buildInitialCepViewState(): CepViewState {
  const summary = cepArtifactStore.summary();
  return buildCepViewStateFromSummary(summary, 'local');
}

function buildCepViewStateFromSummary(summary: ReturnType<typeof cepArtifactStore.summary>, source: CepViewState['source']): CepViewState {
  const selectedKind: CepArtifactKind =
    summary.latestByKind['promotion-request']
      ? 'promotion-request'
      : summary.latestByKind['replay-job']
        ? 'replay-job'
        : 'decision';
  const selectedArtifactId = summary.latestByKind[selectedKind]?.id ?? null;
  return {
    selectedKind,
    selectedArtifactId,
    updatedAt: new Date().toISOString(),
    source,
  };
}

function parseArtifactOrgFilter(searchParams: URLSearchParams): string | null {
  const orgId = searchParams.get('orgId') ?? searchParams.get('organizationId');
  const normalized = orgId?.trim();
  return normalized ? normalized : null;
}

type CepTrustBand = 'low' | 'medium' | 'high';
type CepTrustGovernanceLevel = 'basic' | 'enhanced' | 'full';

type CepTrustPacket = {
  relationshipId?: string;
  revision?: number;
  subjectId?: string;
  objectId?: string;
  relationshipKind?: string;
  governanceLevel?: CepTrustGovernanceLevel;
  authorityChain?: string[];
  evidenceIds?: string[];
  score: number;
  band: CepTrustBand;
  authority?: {
    stewardId?: string;
    consentArtifactIds?: string[];
    delegationChainIds?: string[];
  };
  provenance?: {
    originSystem?: string;
    originActorId?: string;
    method?: string;
    createdAt?: string;
    standardsTraceabilityIds?: string[];
  };
  ledgerEntryId?: string;
  receiptId?: string;
  capturedAt?: string;
};

type CepTrustPolicy = {
  governanceLevel: CepTrustGovernanceLevel;
  minTrustScore: number;
  minTrustBand?: CepTrustBand;
  preferHighTrustBand?: boolean;
};

type CepArtifactTrustFilters = {
  trustBand: CepTrustBand | null;
  minTrustScore: number | null;
  governanceLevel: CepTrustGovernanceLevel | null;
  includeUntrusted: boolean;
};

type CepArtifactViewRecord = CepArtifactRecord & {
  trust?: CepTrustPacket | null;
  trustPolicy?: CepTrustPolicy | null;
};

type CepArtifactSummary = {
  available: boolean;
  storePath: string;
  entryCount: number;
  countsByKind: Record<CepArtifactKind, number>;
  records: CepArtifactViewRecord[];
  latestByKind: Record<CepArtifactKind, CepArtifactViewRecord | null>;
  recentRecords: CepArtifactViewRecord[];
  organizationId?: string | null;
};

type CepTrustSummary = {
  available: boolean;
  trustedCount: number;
  untrustedCount: number;
  lowCount: number;
  mediumCount: number;
  highCount: number;
  averageTrustScore: number | null;
  governanceLevels: Record<CepTrustGovernanceLevel, number>;
};

function parseTrustArtifactFilters(searchParams: URLSearchParams): CepArtifactTrustFilters {
  const trustBand = normalizeTrustBand(searchParams.get('trustBand'));
  const governanceLevel = normalizeTrustGovernanceLevel(searchParams.get('governanceLevel'));
  const minTrustScore = parseTrustScore(searchParams.get('minTrustScore'));
  const includeUntrustedParam = searchParams.get('includeUntrusted');
  const hasTrustConstraint = trustBand !== null || governanceLevel !== null || minTrustScore !== null;
  const includeUntrusted =
    includeUntrustedParam === null ? !hasTrustConstraint : includeUntrustedParam !== 'false';

  return {
    trustBand,
    minTrustScore,
    governanceLevel,
    includeUntrusted,
  };
}

function normalizeTrustBand(value: string | null): CepTrustBand | null {
  if (value === 'low' || value === 'medium' || value === 'high') {
    return value;
  }
  return null;
}

function normalizeTrustGovernanceLevel(value: string | null): CepTrustGovernanceLevel | null {
  if (value === 'basic' || value === 'enhanced' || value === 'full') {
    return value;
  }
  return null;
}

function parseTrustScore(value: string | null): number | null {
  if (!value) {
    return null;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function buildCepArtifactSummary(
  storePath: string,
  records: CepArtifactViewRecord[],
  organizationId?: string | null,
): CepArtifactSummary {
  return {
    available: records.length > 0,
    storePath,
    entryCount: records.length,
    countsByKind: buildCepArtifactKindCounts(records),
    records,
    latestByKind: buildCepArtifactLatestByKind(records),
    recentRecords: records.slice(-8).reverse(),
    organizationId: organizationId ?? null,
  };
}

function buildCepArtifactKindCounts(records: CepArtifactViewRecord[]): Record<CepArtifactKind, number> {
  return CEP_ARTIFACT_KINDS.reduce((counts, kind) => {
    counts[kind] = records.filter((record) => record.kind === kind).length;
    return counts;
  }, { 'promotion-request': 0, 'replay-job': 0, decision: 0 } as Record<CepArtifactKind, number>);
}

function buildCepArtifactLatestByKind(records: CepArtifactViewRecord[]): Record<CepArtifactKind, CepArtifactViewRecord | null> {
  return CEP_ARTIFACT_KINDS.reduce((latest, kind) => {
    const recordsOfKind = records.filter((record) => record.kind === kind);
    latest[kind] = recordsOfKind.length > 0 ? recordsOfKind[recordsOfKind.length - 1] : null;
    return latest;
  }, { 'promotion-request': null, 'replay-job': null, decision: null } as Record<CepArtifactKind, CepArtifactViewRecord | null>);
}

function buildCepTrustSummary(records: CepArtifactViewRecord[]): CepTrustSummary {
  const summary: CepTrustSummary = {
    available: false,
    trustedCount: 0,
    untrustedCount: 0,
    lowCount: 0,
    mediumCount: 0,
    highCount: 0,
    averageTrustScore: null,
    governanceLevels: {
      basic: 0,
      enhanced: 0,
      full: 0,
    },
  };

  let trustScoreTotal = 0;
  let trustScoreCount = 0;
  for (const record of records) {
    const trust = record.trust ?? null;
    if (!trust) {
      summary.untrustedCount += 1;
      continue;
    }

    summary.available = true;
    summary.trustedCount += 1;
    trustScoreTotal += trust.score;
    trustScoreCount += 1;

    if (trust.band === 'low') {
      summary.lowCount += 1;
    } else if (trust.band === 'medium') {
      summary.mediumCount += 1;
    } else {
      summary.highCount += 1;
    }

    if (trust.governanceLevel) {
      summary.governanceLevels[trust.governanceLevel] += 1;
    }
  }

  summary.averageTrustScore = trustScoreCount > 0 ? Number((trustScoreTotal / trustScoreCount).toFixed(4)) : null;
  return summary;
}

function extractCepArtifactTrust(record: CepArtifactRecord): CepTrustPacket | null {
  const payload = record.payload;
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return null;
  }

  const root = payload as Record<string, unknown>;
  const candidates: unknown[] = [
    root.trust,
    root.packet && typeof root.packet === 'object' && !Array.isArray(root.packet) ? (root.packet as Record<string, unknown>).trust : null,
    root.input && typeof root.input === 'object' && !Array.isArray(root.input) && (root.input as Record<string, unknown>).context && typeof (root.input as Record<string, unknown>).context === 'object'
      ? ((root.input as Record<string, unknown>).context as Record<string, unknown>).trust
      : null,
    root.decision && typeof root.decision === 'object' && !Array.isArray(root.decision) && (root.decision as Record<string, unknown>).outcome && typeof (root.decision as Record<string, unknown>).outcome === 'object'
      ? ((root.decision as Record<string, unknown>).outcome as Record<string, unknown>).trust
      : null,
  ];

  for (const candidate of candidates) {
    if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) {
      continue;
    }

    const trust = candidate as Partial<CepTrustPacket>;
    if (typeof trust.score !== 'number' || (trust.band !== 'low' && trust.band !== 'medium' && trust.band !== 'high')) {
      continue;
    }

    return {
      relationshipId: typeof trust.relationshipId === 'string' ? trust.relationshipId : undefined,
      revision: typeof trust.revision === 'number' ? trust.revision : undefined,
      subjectId: typeof trust.subjectId === 'string' ? trust.subjectId : undefined,
      objectId: typeof trust.objectId === 'string' ? trust.objectId : undefined,
      relationshipKind: typeof trust.relationshipKind === 'string' ? trust.relationshipKind : undefined,
      governanceLevel: trust.governanceLevel === 'basic' || trust.governanceLevel === 'enhanced' || trust.governanceLevel === 'full'
        ? trust.governanceLevel
        : undefined,
      authorityChain: Array.isArray(trust.authorityChain) ? trust.authorityChain.filter((entry): entry is string => typeof entry === 'string') : undefined,
      evidenceIds: Array.isArray(trust.evidenceIds) ? trust.evidenceIds.filter((entry): entry is string => typeof entry === 'string') : undefined,
      score: trust.score,
      band: trust.band,
      authority: trust.authority && typeof trust.authority === 'object' && !Array.isArray(trust.authority)
        ? {
            stewardId: typeof trust.authority.stewardId === 'string' ? trust.authority.stewardId : undefined,
            consentArtifactIds: Array.isArray(trust.authority.consentArtifactIds)
              ? trust.authority.consentArtifactIds.filter((entry): entry is string => typeof entry === 'string')
              : undefined,
            delegationChainIds: Array.isArray(trust.authority.delegationChainIds)
              ? trust.authority.delegationChainIds.filter((entry): entry is string => typeof entry === 'string')
              : undefined,
          }
        : undefined,
      provenance: trust.provenance && typeof trust.provenance === 'object' && !Array.isArray(trust.provenance)
        ? {
            originSystem: typeof trust.provenance.originSystem === 'string' ? trust.provenance.originSystem : undefined,
            originActorId: typeof trust.provenance.originActorId === 'string' ? trust.provenance.originActorId : undefined,
            method: typeof trust.provenance.method === 'string' ? trust.provenance.method : undefined,
            createdAt: typeof trust.provenance.createdAt === 'string' ? trust.provenance.createdAt : undefined,
            standardsTraceabilityIds: Array.isArray(trust.provenance.standardsTraceabilityIds)
              ? trust.provenance.standardsTraceabilityIds.filter((entry): entry is string => typeof entry === 'string')
              : undefined,
          }
        : undefined,
      ledgerEntryId: typeof trust.ledgerEntryId === 'string' ? trust.ledgerEntryId : undefined,
      receiptId: typeof trust.receiptId === 'string' ? trust.receiptId : undefined,
      capturedAt: typeof trust.capturedAt === 'string' ? trust.capturedAt : undefined,
    };
  }

  return null;
}

function extractCepArtifactTrustPolicy(record: CepArtifactRecord): CepTrustPolicy | null {
  const payload = record.payload;
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    return null;
  }

  const root = payload as Record<string, unknown>;
  const candidate =
    root.governance && typeof root.governance === 'object' && !Array.isArray(root.governance)
      ? (root.governance as Record<string, unknown>).trustPolicy
      : null;

  if (!candidate || typeof candidate !== 'object' || Array.isArray(candidate)) {
    return null;
  }

  const policy = candidate as Partial<CepTrustPolicy>;
  if (policy.governanceLevel !== 'basic' && policy.governanceLevel !== 'enhanced' && policy.governanceLevel !== 'full') {
    return null;
  }

  return {
    governanceLevel: policy.governanceLevel,
    minTrustScore: typeof policy.minTrustScore === 'number' ? policy.minTrustScore : 0,
    minTrustBand: policy.minTrustBand === 'low' || policy.minTrustBand === 'medium' || policy.minTrustBand === 'high' ? policy.minTrustBand : undefined,
    preferHighTrustBand: typeof policy.preferHighTrustBand === 'boolean' ? policy.preferHighTrustBand : undefined,
  };
}

function enrichCepArtifactRecord(record: CepArtifactRecord): CepArtifactViewRecord {
  return {
    ...record,
    trust: extractCepArtifactTrust(record),
    trustPolicy: extractCepArtifactTrustPolicy(record),
  };
}

function artifactMatchesTrustFilters(record: CepArtifactViewRecord, filters: CepArtifactTrustFilters): boolean {
  if (!filters.trustBand && filters.minTrustScore === null && !filters.governanceLevel) {
    return true;
  }

  if (!record.trust) {
    return filters.includeUntrusted;
  }

  if (filters.trustBand && record.trust.band !== filters.trustBand) {
    return false;
  }

  if (filters.minTrustScore !== null && record.trust.score < filters.minTrustScore) {
    return false;
  }

  if (filters.governanceLevel && record.trust.governanceLevel !== filters.governanceLevel) {
    return false;
  }

  return true;
}

function seedCepArtifactsIfNeeded(): void {
  if (cepArtifactStore.summary().entryCount > 0) {
    return;
  }

  const promotionRequest = cepArtifactStore.appendPromotionRequest({
    type: 'PromotionRequest',
    version: '1.0',
    agentId: 'ops-console-seed',
    snapshot: {
      drift: 0.03,
      evidenceCount: 12,
      lineageDepth: 8,
    },
    evidenceSample: [
      {
        source: 'ops-console',
        payload: { receiptId: seededCenResult.receipt.receiptId, verdict: seededCenResult.receipt.verdict },
        timestamp: seededCenResult.receipt.issuedAt,
      },
    ],
    lineageSample: [
      {
        eventType: 'request_queued',
        timestamp: seededCenResult.receipt.issuedAt,
      },
    ],
    requestedChange: {
      kind: 'CapabilityPromotion',
      capabilityId: 'remote-ide-v1',
      reason: 'Seeded promotion request for remote orchestrator viewer.',
    },
  });

  const replayJob = cepArtifactStore.appendReplayJob({
    type: 'ReplayJob',
    version: '1.0',
    agentId: 'ops-console-seed',
    timelineId: 'ops-console-timeline',
    window: {
      startTime: seededCenResult.receipt.issuedAt,
      endTime: new Date().toISOString(),
    },
    checks: ['DRIFT_BOUND_V1', 'EVIDENCE_SUFFICIENCY_V1', 'LINEAGE_CONTINUITY_V1'],
  }, {
    relatedArtifactId: promotionRequest.id,
    title: 'Promotion Replay Job',
  });

  const decision = cepArtifactStore.appendDecision({
    type: 'PromotionDecision',
    version: '1.0',
    decisionId: 'PROMO-SEED-0001',
    agentId: 'ops-console-seed',
    capabilityId: 'remote-ide-v1',
    status: 'APPROVED',
    evidenceRef: 'seed-evidence',
    lineageRef: 'seed-lineage',
    replayRef: replayJob.id,
    conformanceRef: 'seed-conformance',
    timestamp: new Date().toISOString(),
  }, {
    relatedArtifactId: replayJob.id,
    title: 'Promotion Decision',
  });

  cepViewState = {
    selectedKind: 'decision',
    selectedArtifactId: decision.id,
    updatedAt: new Date().toISOString(),
    source: 'local',
  };
}

function parseCepArtifactKind(value: string): CepArtifactKind | null {
  if (value === 'promotion-request' || value === 'replay-job' || value === 'decision') {
    return value;
  }
  return null;
}

const evidenceGraph = buildEvidenceGraph();
app.use((req, res, next) => {
  const requestId = req.header('x-request-id') ?? `req-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  res.setHeader('x-request-id', requestId);
  res.setHeader('x-content-type-options', 'nosniff');
  res.setHeader('x-frame-options', 'DENY');
  res.setHeader('referrer-policy', 'no-referrer');
  next();
});
app.use(express.json({ limit: '1mb' }));

app.use('/proof-surfaces', (req, res, next) => {
  res.setHeader('access-control-allow-origin', '*');
  res.setHeader('access-control-allow-methods', 'GET, OPTIONS');
  res.setHeader('access-control-allow-headers', 'content-type, accept');
  if (req.method === 'OPTIONS') {
    res.status(204).end();
    return;
  }
  next();
});

app.get('/health', (_req, res) => {
  res.json({ ok: true });
});

app.get('/readiness', (_req, res) => {
  const checks = {
    telemetry: faultJournal.getAll().length > 0,
    cen: cenReceipts.size > 0,
    sovereigntyLedger: sovereigntyLedger.entries().length > 0,
    lawOfLawsLedger: lawOfLawsLedger.entries().length > 0,
  };
  res.json({
    ready: Object.values(checks).every(Boolean),
    checks,
  });
});

app.get('/telemetry', async (_req, res) => {
  const faults = faultJournal.getAll();
  const patterns = patternLedger.getAll();
  const drift = new DriftMetrics().computeDrift(faults, patterns);
  const aais = await getAaisTelemetryStatus();
  const sovereignxHardware = captureSovereignXHardwareSnapshot();
  const sovereignxClusterSnapshot = buildSovereignXClusterGovernanceSnapshot(sovereignxHardware);
  const hardwareBenchmarks = buildSovereignXHardwareBenchmarks(sovereignxHardware);
  const proofSurfaces = listOpsConsoleProofSurfaces(sovereignxHardware);
  const replayValidation = buildSovereignXHardwareReplayValidationSummary();
  const pricing = summarizePricingLedger();
  res.json({
    drift,
    topPatterns: patternLedger.getTopRecurring(5),
    lastFaults: faults.slice(-10).reverse(),
    patchTimeline: patchAnalytics.getTimeline(),
    cab: getCabTelemetrySummary(),
    aais,
    sovereignxHardware,
    sovereignxClusterRouting: sovereignxClusterSnapshot.clusterRouting,
    sovereignxClusterGovernance: sovereignxClusterSnapshot.clusterGovernance,
    thermalBridge: sovereignxHardware.thermalBridge,
    hardwareBenchmarks,
    overrideDrill: buildSovereignXHardwareOverrideDrill(sovereignxHardware),
    hardwareReplayStore: sovereignXHardwareReplayStore.summary(),
    replayValidation,
    constitutionalTraceability: sovereignxClusterSnapshot.clusterGovernance.traceabilityMatrix,
    evidenceGraph: summarizeConstitutionalEvidenceGraph(evidenceGraph),
    proofSurfaces: summarizeOpsConsoleProofSurfaces(proofSurfaces),
    pricing,
  });
});

const cepArtifactListPaths = ['/cep/artifacts', '/api/cep/artifacts'];
const cepArtifactExportPaths = ['/cep/artifacts/export.json', '/api/cep/artifacts/export.json'];
const cepArtifactKindPaths = ['/cep/artifacts/:kind', '/api/cep/artifacts/:kind'];
const cepArtifactDetailPaths = ['/cep/artifacts/:kind/:artifactId', '/api/cep/artifacts/:kind/:artifactId'];
const cepViewStatePaths = ['/cep/view-state', '/api/cep/view-state'];

app.get(cepArtifactListPaths, (_req, res) => {
  const searchParams = new URLSearchParams(_req.url.split('?')[1] ?? '');
  const organizationId = parseArtifactOrgFilter(searchParams);
  const trustFilters = parseTrustArtifactFilters(searchParams);
  const exported = cepArtifactStore.exportJson(organizationId ?? undefined);
  const records = exported.records
    .map(enrichCepArtifactRecord)
    .filter((artifact) => artifactMatchesTrustFilters(artifact, trustFilters));
  const summary = buildCepArtifactSummary(exported.storePath, records, organizationId);
  res.json({
    viewState: organizationId ? buildCepViewStateFromSummary(summary, 'remote') : cepViewState,
    ...summary,
    organizationId,
    trustFilters,
    trustSummary: buildCepTrustSummary(records),
  });
});

app.get(cepArtifactExportPaths, (_req, res) => {
  const searchParams = new URLSearchParams(_req.url.split('?')[1] ?? '');
  const organizationId = parseArtifactOrgFilter(searchParams);
  const trustFilters = parseTrustArtifactFilters(searchParams);
  const exported = cepArtifactStore.exportJson(organizationId ?? undefined);
  const records = exported.records
    .map(enrichCepArtifactRecord)
    .filter((artifact) => artifactMatchesTrustFilters(artifact, trustFilters));
  const summary = buildCepArtifactSummary(exported.storePath, records, organizationId);
  res.json({
    viewState: organizationId ? buildCepViewStateFromSummary(summary, 'remote') : cepViewState,
    ...summary,
    organizationId,
    trustFilters,
    trustSummary: buildCepTrustSummary(records),
  });
});

app.get(cepArtifactKindPaths, (req, res) => {
  const kind = parseCepArtifactKind(String(req.params.kind));
  if (!kind) {
    res.status(400).json({ error: 'unsupported CEP artifact kind' });
    return;
  }
  const searchParams = new URLSearchParams(req.url.split('?')[1] ?? '');
  const organizationId = parseArtifactOrgFilter(searchParams);
  const trustFilters = parseTrustArtifactFilters(searchParams);
  const artifacts = cepArtifactStore
    .list(undefined, organizationId ?? undefined)
    .filter((artifact) => artifact.kind === kind)
    .map(enrichCepArtifactRecord)
    .filter((artifact) => artifactMatchesTrustFilters(artifact, trustFilters));
  res.json({
    kind,
    artifacts,
    viewState: organizationId ? buildCepViewStateFromSummary(buildCepArtifactSummary(cepArtifactStore.exportJson(organizationId ?? undefined).storePath, artifacts, organizationId), 'remote') : cepViewState,
    organizationId,
    trustFilters,
    trustSummary: buildCepTrustSummary(artifacts),
  });
});

app.get(cepArtifactDetailPaths, (req, res) => {
  const kind = parseCepArtifactKind(String(req.params.kind));
  if (!kind) {
    res.status(400).json({ error: 'unsupported CEP artifact kind' });
    return;
  }
  const searchParams = new URLSearchParams(req.url.split('?')[1] ?? '');
  const organizationId = parseArtifactOrgFilter(searchParams);
  const trustFilters = parseTrustArtifactFilters(searchParams);
  const artifact = cepArtifactStore.getArtifact(String(req.params.artifactId));
  const enrichedArtifact = artifact ? enrichCepArtifactRecord(artifact) : null;
  if (!artifact || artifact.kind !== kind || (organizationId && artifact.organizationId !== organizationId) || !enrichedArtifact || !artifactMatchesTrustFilters(enrichedArtifact, trustFilters)) {
    res.status(404).json({ error: 'CEP artifact not found' });
    return;
  }
  const auditPublicKey = process.env.AUDIT_PUBLIC_KEY ?? process.env.AUDIT_PUBLIC_KEY_PEM ?? '';
  res.json({
    artifact: enrichedArtifact,
    signatureVerified: auditPublicKey.trim() ? verifyCepArtifactSignature(artifact, auditPublicKey) : undefined,
    viewState: {
      selectedKind: kind,
      selectedArtifactId: artifact.id,
      updatedAt: new Date().toISOString(),
      source: 'remote',
    },
    organizationId,
    trustFilters,
    trustSummary: buildCepTrustSummary([enrichedArtifact]),
  });
});

app.post(cepArtifactKindPaths, (req, res) => {
  const kind = parseCepArtifactKind(String(req.params.kind));
  if (!kind) {
    res.status(400).json({ error: 'unsupported CEP artifact kind' });
    return;
  }

  const body = req.body as {
    id?: string;
    title?: string;
    source?: string;
    organizationId?: string;
    relatedArtifactId?: string;
    signature?: string;
    payload?: unknown;
  } | undefined;
  const payload = body?.payload ?? body ?? {};
  const title =
    body?.title ??
    (kind === 'promotion-request'
      ? 'Promotion Request'
      : kind === 'replay-job'
        ? 'Replay Job'
        : 'Decision');

  const artifact = cepArtifactStore.append({
    kind,
    id: body?.id,
    title,
    source: body?.source ?? 'remote',
    organizationId: body?.organizationId ?? (typeof payload === 'object' && payload && 'organizationId' in payload ? String((payload as { organizationId?: string }).organizationId ?? '') || undefined : undefined),
    relatedArtifactId: body?.relatedArtifactId,
    signature: body?.signature,
    payload,
  });
  cepViewState = {
    selectedKind: kind,
    selectedArtifactId: artifact.id,
    updatedAt: new Date().toISOString(),
    source: 'remote',
  };
  res.status(201).json({
    artifact,
    viewState: cepViewState,
    summary: cepArtifactStore.summary(),
  });
});

app.get(cepViewStatePaths, (_req, res) => {
  res.json({ viewState: cepViewState });
});

app.get('/cori-alpha/summary', (_req, res) => {
  res.json({ surface: getCoriAlphaWorkspaceSummary() });
});

app.patch(cepViewStatePaths, (req, res) => {
  const body = req.body as { selectedKind?: string; selectedArtifactId?: string | null } | undefined;
  const nextKind = body?.selectedKind ? parseCepArtifactKind(body.selectedKind) : null;
  const selectedKind = nextKind ?? cepViewState.selectedKind;
  const selectedArtifactId = body?.selectedArtifactId ?? cepViewState.selectedArtifactId;
  cepViewState = {
    selectedKind,
    selectedArtifactId,
    updatedAt: new Date().toISOString(),
    source: 'remote',
  };
  res.json({ viewState: cepViewState });
});

app.get('/sovereignx/hardware', (_req, res) => {
  const snapshot = captureSovereignXHardwareSnapshot();
  const benchmarks = buildSovereignXHardwareBenchmarks(snapshot);
  res.json({
    ...snapshot,
    replayStore: sovereignXHardwareReplayStore.summary(),
    overrideDrill: buildSovereignXHardwareOverrideDrill(snapshot),
    replayValidation: buildSovereignXHardwareReplayValidationSummary(),
    benchmarks,
  });
});

app.get('/hardware/summary', (_req, res) => {
  res.json(buildHardwareConsoleDashboard());
});

app.get('/hardware/stream', (req, res) => {
  res.writeHead(200, {
    'content-type': 'text/event-stream; charset=utf-8',
    'cache-control': 'no-cache, no-transform',
    connection: 'keep-alive',
  });
  res.write(`event: summary\n`);
  res.write(`data: ${JSON.stringify(buildHardwareConsoleDashboard())}\n\n`);

  const interval = setInterval(() => {
    res.write(`event: summary\n`);
    res.write(`data: ${JSON.stringify(buildHardwareConsoleDashboard())}\n\n`);
  }, 4000);

  req.on('close', () => {
    clearInterval(interval);
  });
});

app.post('/hardware/replay', (req, res) => {
  const body = (req.body ?? {}) as {
    workloadId?: string;
    currentRoute?: 'cpu' | 'gpu';
    counterfactualRoute?: 'cpu' | 'gpu';
  };

  if (!body.workloadId || !body.currentRoute || !body.counterfactualRoute) {
    res.status(400).json({ error: 'workloadId, currentRoute, and counterfactualRoute are required' });
    return;
  }

  const snapshot = captureSovereignXHardwareSnapshot();
  const clusterSnapshot = buildSovereignXClusterGovernanceSnapshot(snapshot);
  const benchmarkSpec = buildHardwareBenchmarkCatalog()[0];
  const currentMetrics = estimateHardwareBenchmarkMetrics(snapshot, clusterSnapshot.clusterRouting, benchmarkSpec, body.currentRoute);
  const counterfactualMetrics = estimateHardwareBenchmarkMetrics(snapshot, clusterSnapshot.clusterRouting, benchmarkSpec, body.counterfactualRoute);
  const comparison = buildHardwareReplayComparison(
    body.workloadId,
    body.currentRoute,
    body.counterfactualRoute,
    currentMetrics,
    counterfactualMetrics,
  );
  const artifact = hardwareEvidenceStore.appendReplay({
    artifactType: 'HardwareReplayEvidenceArtifact',
    workloadId: body.workloadId,
    currentRoute: body.currentRoute,
    counterfactualRoute: body.counterfactualRoute,
    comparison,
    evidenceRefs: buildHardwareEvidenceContext()?.replayArtifactIds ?? [],
  });

  res.json({
    artifact,
    comparison,
    summary: hardwareEvidenceStore.summary(),
  });
});

app.post('/hardware/benchmarks/run', (req, res) => {
  const body = (req.body ?? {}) as {
    benchmarkId?: string;
    route?: HardwareRoute;
    routes?: HardwareRoute[];
  };

  const benchmarkSpecs = buildHardwareBenchmarkCatalog();
  const benchmarkSpec = benchmarkSpecs.find((spec) => spec.id === body.benchmarkId) ?? benchmarkSpecs[0];
  const requestedRoutes = Array.from(new Set((body.routes ?? (body.route ? [body.route] : benchmarkSpec.targetRoutes)).filter(Boolean)));
  const snapshot = captureSovereignXHardwareSnapshot();
  const clusterSnapshot = buildSovereignXClusterGovernanceSnapshot(snapshot);
  const runs = requestedRoutes.map((route) => {
    const metrics = estimateHardwareBenchmarkMetrics(snapshot, clusterSnapshot.clusterRouting, benchmarkSpec, route);
    const artifact = hardwareEvidenceStore.appendBenchmark({
      artifactType: 'HardwareBenchmarkArtifact',
      benchmarkSpec,
      route,
      metrics,
      evidenceRefs: buildHardwareEvidenceContext()?.benchmarkArtifactIds ?? [],
    });
    return {
      artifact,
      metrics,
    };
  });

  res.json({
    benchmarkSpec,
    runs,
    summary: hardwareEvidenceStore.summary(),
  });
});

app.get('/sovereignx/hardware/benchmarks', (_req, res) => {
  const snapshot = captureSovereignXHardwareSnapshot();
  res.json(buildSovereignXHardwareBenchmarks(snapshot));
});

app.get('/sovereignx/cluster-routing', (_req, res) => {
  const snapshot = captureSovereignXHardwareSnapshot();
  const clusterGovernanceSnapshot = buildSovereignXClusterGovernanceSnapshot(snapshot);
  res.json({
    hardware: snapshot,
    clusterRouting: clusterGovernanceSnapshot.clusterRouting,
    clusterGovernance: clusterGovernanceSnapshot.clusterGovernance,
  });
});

app.get('/sovereignx/cluster-membership', (_req, res) => {
  const snapshot = captureSovereignXHardwareSnapshot();
  const clusterGovernanceSnapshot = buildSovereignXClusterGovernanceSnapshot(snapshot);
  res.json({
    hardware: snapshot,
    clusterRouting: clusterGovernanceSnapshot.clusterRouting,
    clusterGovernance: clusterGovernanceSnapshot.clusterGovernance,
  });
});

app.post('/sovereignx/cluster-membership/control', (req, res) => {
  const snapshot = captureSovereignXHardwareSnapshot();
  const request = (req.body ?? {}) as SovereignXClusterControlRequest;
  const controlState = applySovereignXClusterControlRequest(request, snapshot.governor.state.lastUpdatedAtMs);
  const clusterGovernanceSnapshot = buildSovereignXClusterGovernanceSnapshot(snapshot);
  const clusterGovernance = buildSovereignXClusterGovernanceProjection(
    clusterGovernanceSnapshot.router,
    clusterGovernanceSnapshot.request,
    clusterGovernanceSnapshot.clusterRouting,
    snapshot,
    controlState,
  );
  res.json({
    hardware: snapshot,
    controlState,
    clusterRouting: clusterGovernanceSnapshot.clusterRouting,
    clusterGovernance,
    traceabilityMatrix: clusterGovernance.traceabilityMatrix,
  });
});

app.get('/sovereignx/cluster-membership/validation', (_req, res) => {
  const snapshot = captureSovereignXHardwareSnapshot();
  const clusterGovernanceSnapshot = buildSovereignXClusterGovernanceSnapshot(snapshot);
  res.json({
    clusterGovernance: clusterGovernanceSnapshot.clusterGovernance,
    soakChaosValidation: clusterGovernanceSnapshot.clusterGovernance.soakChaosValidation,
  });
});

app.get('/constitutional-traceability', (_req, res) => {
  const snapshot = captureSovereignXHardwareSnapshot();
  const clusterGovernanceSnapshot = buildSovereignXClusterGovernanceSnapshot(snapshot);
  res.json({
    matrix: clusterGovernanceSnapshot.clusterGovernance.traceabilityMatrix,
    clusterGovernance: clusterGovernanceSnapshot.clusterGovernance,
  });
});

app.get('/sovereignx/hardware/thermal-bridge', (_req, res) => {
  res.json(sovereignXThermalBridge.snapshot());
});

app.post('/sovereignx/hardware/override-drill', (req, res) => {
  const snapshot = captureSovereignXHardwareSnapshot();
  const body = req.body as SovereignXHardwareOverrideDrillRequest | undefined;
  res.json({
    snapshot,
    drill: runSovereignXHardwareOverrideDrill(snapshot, body ?? {}),
    replayStore: sovereignXHardwareReplayStore.summary(),
  });
});

app.get('/sovereignx/hardware/replay', (_req, res) => {
  res.json(sovereignXHardwareReplayStore.summary());
});

app.get('/sovereignx/hardware/replay/validation', (_req, res) => {
  res.json(buildSovereignXHardwareReplayValidationSummary());
});

app.get('/proof-surfaces', (_req, res) => {
  const hardwareSnapshot = captureSovereignXHardwareSnapshot();
  const records = listOpsConsoleProofSurfaces(hardwareSnapshot);
  res.json({
    catalog: createProofSurfaceCatalogDocument(records),
    records,
    summaries: summarizeOpsConsoleProofSurfaces(records),
  });
});

app.get('/constitutional-release-receipt', (_req, res) => {
  const receipt = evidenceGraph.rootReceipt;
  res.json({ receipt });
});

app.get('/evidence-graph', (_req, res) => {
  res.json({ graph: evidenceGraph, summary: summarizeConstitutionalEvidenceGraph(evidenceGraph) });
});

app.get('/governance', (_req, res) => {
  res.json(governanceAdapter.snapshot());
});

app.get('/ledger', (_req, res) => {
  res.json(ledgerAdapter.snapshot());
});

app.get('/pricing/ledger', (_req, res) => {
  res.json(summarizePricingLedger());
});

app.get('/pricing/reports', (_req, res) => {
  res.json(summarizePricingLedger());
});

app.get('/pricing/reports/margin.csv', (_req, res) => {
  res.setHeader('content-type', 'text/csv; charset=utf-8');
  res.send(renderPricingMarginReportCsv());
});

app.get('/pricing/reports/cohorts.csv', (_req, res) => {
  res.setHeader('content-type', 'text/csv; charset=utf-8');
  res.send(renderPricingCohortHistoryCsv());
});

app.get('/pricing/cohorts', (_req, res) => {
  const summary = summarizePricingLedger();
  res.json({ cohortHistory: summary.cohortHistory });
});

app.get('/customers', async (_req, res) => {
  const customers = await fetchPlatformCustomers();
  res.json({
    customers,
    customerCount: customers.length,
    planCounts: customers.reduce<Record<string, number>>((counts, customer) => {
      counts[customer.planId] = (counts[customer.planId] ?? 0) + 1;
      return counts;
    }, {}),
  });
});

app.get('/organizations', async (_req, res) => {
  const organizations = await fetchPlatformOrganizations();
  const roleCounts = organizations.reduce<Record<string, number>>((counts, organization) => {
    for (const member of organization.members) {
      counts[member.role] = (counts[member.role] ?? 0) + 1;
    }
    return counts;
  }, {});
  res.json({
    organizations,
    organizationCount: organizations.length,
    roleCounts,
  });
});

app.get('/customers/quota', async (_req, res) => {
  const quota = await fetchPlatformQuota();
  if (!quota) {
    res.status(502).json({ error: 'customer quota unavailable' });
    return;
  }
  res.json(quota);
});

app.get('/treasury/schedule', async (_req, res) => {
  const schedule = await fetchPlatformTreasurySchedule();
  if (!schedule) {
    res.status(502).json({ error: 'treasury schedule unavailable' });
    return;
  }
  res.json({ schedule });
});

app.get('/organizations/:organizationId/usage', async (req, res) => {
  const usage = await fetchPlatformOrganizationUsage(String(req.params.organizationId));
  if (!usage) {
    res.status(502).json({ error: 'organization usage unavailable' });
    return;
  }
  res.json(usage);
});

app.get('/organizations/:organizationId/audit', async (req, res) => {
  const audit = await fetchPlatformOrganizationAudit(String(req.params.organizationId));
  if (!audit) {
    res.status(502).json({ error: 'organization audit unavailable' });
    return;
  }
  res.json(audit);
});

app.post('/pricing/ledger', (req, res) => {
  try {
    const body = req.body as
      | Parameters<typeof createPricingLedgerEntryResponse>[0]
      | { entry?: Parameters<typeof createPricingLedgerEntryResponse>[0] }
      | undefined;
    const entry = (typeof body === 'object' && body !== null && 'entry' in body
      ? body.entry
      : body) as Parameters<typeof createPricingLedgerEntryResponse>[0] | undefined;
    if (!entry) {
      res.status(400).json({ error: 'pricing ledger entry is required' });
      return;
    }

    const response = createPricingLedgerEntryResponse(entry);
    res.status(201).json(response);
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.get('/faults', (_req, res) => {
  res.json(faultAdapter.snapshot());
});

app.get('/runtime', (_req, res) => {
  res.json(runtimeAdapter.snapshot());
});

app.get('/substrate', (_req, res) => {
  res.json(substrateAdapter.snapshot());
});

app.get('/aais/health', async (_req, res) => {
  res.json({ aais: await getAaisTelemetryStatus() });
});

app.get('/mri', (_req, res) => {
  res.json(getSeededMriAssessment());
});

app.get('/mri/v2', (_req, res) => {
  res.json(getSeededMriAssessmentV2());
});

app.get('/coverage', (_req, res) => {
  const coverage = getSubsystemCoverage();
  res.json({
    inventory: coverage.inventory,
    mappedDocuments: coverage.documents.length,
    subsystems: Array.from(new Set(coverage.documents.map((doc) => doc.subsystem))).sort(),
    documents: coverage.documents,
  });
});

app.get('/cen/demo', (_req, res) => {
  res.json(seededCenResult);
});

app.get('/cen/events', (_req, res) => {
  res.json({
    status: 'ACTIVE',
    invariantSet: { active: 6, disabled: 0 },
    tokenCounts: { VT: 1, FT: 1, MRT: 1, RT: 1 },
    enforcementRatePerMinute: 14.2,
    replayAttemptsBlocked: 1,
    events: Array.from(cenReceipts.values()),
  });
});

app.get('/cen/receipts/:receiptId', (req, res) => {
  const receipt = cenReceipts.get(req.params.receiptId);
  if (!receipt) {
    res.status(404).json({ error: 'receipt not found' });
    return;
  }
  res.json({ receipt });
});

app.get('/sovereignty-ledger', (_req, res) => {
  res.json({ entries: sovereigntyLedger.entries() });
});

app.get('/nimf/forecast', (_req, res) => {
  res.json({ forecast: forecastTrajectory(getSeededMriAssessmentV2(), 3) });
});

app.post('/evolution/propose', (req, res) => {
  const body = req.body as { invariantId?: string; expression?: string };
  res.json({
    proposal: proposeInvariant({
      invariantId: body.invariantId ?? 'INV-OPS',
      expression: body.expression ?? 'require governance >= 70',
      mode: 'Genesis',
    }),
  });
});

app.post('/evolution/evaluate', (req, res) => {
  const body = req.body as { invariantId?: string; expression?: string };
  const proposal = proposeInvariant({
    invariantId: body.invariantId ?? 'INV-OPS',
    expression: body.expression ?? 'require governance >= 70',
    mode: 'Genesis',
  });
  res.json({ decision: evaluateInvariantFitness({ proposal, mri: getSeededMriAssessmentV2() }) });
});

app.get('/evolution/timeline', (_req, res) => {
  res.json(governanceEvolutionTimeline);
});

app.get('/pod/meta_constitutional_collapse', (_req, res) => {
  res.json({
    pod: recordMetaConstitutionalCollapsePod(),
    collapse: collapseGovernanceLayers(),
  });
});

app.get('/meta/law-of-laws', (_req, res) => {
  res.json({ entries: lawOfLawsLedger.entries() });
});

app.get('/patches', (_req, res) => {
  res.json({ patches: listPatches() });
});

app.get('/arena', (_req, res) => {
  res.json(createArenaModeSnapshot());
});

app.post('/patches/:patchId/approve', (req, res) => {
  try {
    const actor = (req.body as { actor?: string })?.actor ?? 'operator';
    const record = approvePatch(req.params.patchId, actor);
    res.json({ patch: record });
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.post('/patches/:patchId/reject', (req, res) => {
  try {
    const record = rejectPatch(req.params.patchId);
    res.json({ patch: record });
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

app.post('/patches/:patchId/deploy', (req, res) => {
  try {
    const record = deployPatch(req.params.patchId);
    res.json({ patch: record });
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
  }
});

function buildGovernanceEvolutionTimeline(): GovernanceEvolutionTimeline {
  const proposal = proposeInvariant({
    invariantId: 'INV-OPS',
    expression: 'require governance >= 70',
    mode: 'Genesis',
  });
  const evaluation = evaluateInvariantFitness({ proposal, mri: getSeededMriAssessmentV2() });
  const lawEntries = lawOfLawsLedger.entries();
  const continuityChain = lawEntries.map((entry) => ({
    sequence: entry.sequence,
    entryType: entry.entryType,
    subjectId: entry.subjectId,
    issuedAt: entry.issuedAt,
    entryHash: entry.entryHash,
    previousHash: entry.previousHash,
  }));
  const continuityReport = {
    reportId: `continuity-${evaluation.lawOfLawsEntry.entryHash.slice(0, 16)}`,
    createdAt: evaluation.receipt.issuedAt,
    valid: lawEntries.length > 0,
    lineageValid: lawEntries.length > 0,
    replayValid: evaluation.decision !== 'revert',
    receiptId: evaluation.receipt.receiptId,
    notes: [
      'Lineage chain preserved through the Law of Laws ledger.',
      'Replay validation linked the amendment to a constitutional evidence receipt.',
    ],
    chain: continuityChain,
  };
  const governanceDiff = {
    diffId: `gov-diff-${evaluation.lawOfLawsEntry.entryHash.slice(0, 16)}`,
    createdAt: evaluation.receipt.issuedAt,
    currentConfigVersion: 'v1.0.0',
    targetConfigVersion: 'v1.1.0',
    domain: 'governance',
    tier: 'constitutional',
    changes: [
      {
        path: 'thresholds.minTrustScore',
        before: 0.7,
        after: 0.78,
        rationale: 'Raise the trust floor after replay-backed governance review.',
      },
      {
        path: 'delegationRules.maxChainLength',
        before: 3,
        after: 2,
        rationale: 'Shorten delegation chains to keep authority traceable.',
      },
    ],
    replayReportIds: [evaluation.receipt.receiptId],
    trustReportIds: [seededCenResult.receipt.receiptId],
  };

  const entries: GovernanceEvolutionTimelineEntry[] = [
    {
      eventId: 'governance-evolution-boot',
      stage: 'birth',
      artifactId: 'constitutional-birth',
      createdAt: '2026-06-18T22:02:00.000Z',
      summary: 'Constitutional lineage was initialized and anchored in the law-of-laws ledger.',
      outcome: 'proposed',
      continuityReport: {
        ...continuityReport,
        reportId: 'continuity-boot',
        notes: [...continuityReport.notes, 'Birth event established the first stable lineage chain.'],
      },
      governanceDiff: null,
      replayReport: null,
    },
    {
      eventId: 'governance-evolution-review',
      stage: 'governance',
      artifactId: proposal.invariantId,
      createdAt: evaluation.receipt.issuedAt,
      summary: 'The steward proposed a governance amendment after evaluating replay evidence.',
      outcome: 'proposed',
      continuityReport,
      governanceDiff,
      replayReport: null,
    },
    {
      eventId: 'governance-evolution-replay',
      stage: 'replay',
      artifactId: evaluation.receipt.receiptId,
      createdAt: evaluation.receipt.issuedAt,
      summary: 'Historical replay validated the amendment path and preserved continuity.',
      outcome: 'replayed',
      continuityReport: {
        ...continuityReport,
        reportId: 'continuity-replay',
        replayValid: true,
        notes: [...continuityReport.notes, `Replay decision ${evaluation.decision} confirmed the amendment path.`],
      },
      governanceDiff,
      replayReport: {
        replayId: `replay-${evaluation.receipt.receiptId}`,
        mode: evaluation.mode,
        decision: evaluation.decision,
        stage: evaluation.stage,
        summary: `Replay returned ${evaluation.decision} with a ${evaluation.stage} stage verdict.`,
        receiptId: evaluation.receipt.receiptId,
        lawOfLawsEntryId: evaluation.lawOfLawsEntry.entryHash,
      },
    },
    {
      eventId: 'governance-evolution-renewal',
      stage: 'renewal',
      artifactId: evaluation.lawOfLawsEntry.entryHash,
      createdAt: evaluation.lawOfLawsEntry.issuedAt,
      summary: 'The amendment outcome was recorded into the constitutional timeline.',
      outcome: 'validated',
      continuityReport: {
        ...continuityReport,
        reportId: 'continuity-renewal',
        notes: [...continuityReport.notes, 'Renewal event recorded the approved lineage outcome.'],
      },
      governanceDiff: {
        ...governanceDiff,
        diffId: `${governanceDiff.diffId}-approved`,
      },
      replayReport: {
        replayId: `replay-${evaluation.receipt.receiptId}-approved`,
        mode: evaluation.mode,
        decision: evaluation.decision,
        stage: evaluation.stage,
        summary: 'The amendment was promoted after continuity and replay validation passed.',
        receiptId: evaluation.receipt.receiptId,
        lawOfLawsEntryId: evaluation.lawOfLawsEntry.entryHash,
      },
    },
  ];

  return {
    timelineId: 'governance-evolution-timeline',
    entries,
    summary: {
      entryCount: entries.length,
      continuityReports: entries.filter((entry) => entry.continuityReport.valid).length,
      governanceDiffs: entries.filter((entry) => entry.governanceDiff !== null).length,
      replayReports: entries.filter((entry) => entry.replayReport !== null).length,
      validatedAmendments: entries.filter((entry) => entry.outcome === 'validated').length,
    },
  };
}

if (existsSync(clientDistDir)) {
  app.use(express.static(clientDistDir));
}

app.use((error: unknown, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
  res.status(400).json({ error: error instanceof Error ? error.message : String(error) });
});

if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => {
    console.log(`AAES-OS ops-console listening on http://localhost:${PORT}`);
    console.log(`  GET /telemetry`);
  });
}

export { app };
