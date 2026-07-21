import React, { useEffect, useMemo, useState, type FormEvent } from 'react';

import type { ConstitutionalEvidenceGraphSummary, ProofSurfaceSummary } from '@aaes-os/aaes-governance';
import { ArenaModePanel } from './ArenaModePanel.js';
import { createArenaModeSnapshot, type ArenaSnapshot } from './arenaMode.js';
import { CepArtifactDock } from './ui/cep-artifacts/CepArtifactDock.js';
import { CustomerQuotaEnforcementPanel } from './ui/customer-quota/CustomerQuotaEnforcementPanel.js';
import { ConstitutionalEvidenceGraphPanel } from './ui/evidence-graph/ConstitutionalEvidenceGraphPanel.js';
import { CoriAlphaSummaryCard, type CoriAlphaWorkspaceSummary } from './coriAlphaSummary.js';
import { GovernanceEvolutionTimelinePanel } from './ui/governance-evolution/GovernanceEvolutionTimelinePanel.js';
import { OrganizationRegistryRbacPanel } from './ui/organization-registry/OrganizationRegistryRbacPanel.js';
import { OrganizationUsageAndAuditPanel } from './ui/organization-usage/OrganizationUsageAndAuditPanel.js';
import { PricingLedgerAndMarginDashboard } from './ui/pricing-ledger/PricingLedgerAndMarginDashboard.js';
import { TreasurySchedulePanel } from './ui/treasury-schedule/TreasurySchedulePanel.js';
import { PatchApprovals } from './PatchApprovals.js';
import type { HardwareConsoleSummary } from './hardwareConsole.js';
import { HardwareConsolePage } from './ui/hardware-console/HardwareConsolePage.js';
import {
  DEFAULT_PROOF_SURFACE_CATALOG_URL,
  PROOF_SURFACE_CATALOG_STORAGE_KEY,
  resolveInitialProofSurfaceCatalogUrl,
  normalizeProofSurfaceCatalogUrl,
} from './catalogConfig.js';

type DriftScore = {
  score: number;
  totalFaults: number;
  uniquePatterns: number;
  topPatterns?: PatternRecord[];
};

type PatternRecord = {
  patternId: string;
  faultCodes: string[];
  invariantIds?: string[];
  recurrence: number;
  firstSeenAt: string;
  lastSeenAt: string;
};

type FaultEvent = {
  faultId: string;
  runId: string;
  spanId: string;
  invariantId?: string;
  timestamp: string;
  faultCode: string;
  severity: string;
};

type PatchPoint = {
  patchId: string;
  timestamp: string;
  effectiveness: number;
};

type TelemetryResponse = {
  drift: DriftScore;
  topPatterns: PatternRecord[];
  lastFaults: FaultEvent[];
  patchTimeline?: PatchPoint[];
  sovereignxHardware?: {
    source: string;
    sourceDetail: string;
    telemetry: {
      cpuTempC: number;
      gpuTempC: number;
      cpuVolt: number;
      gpuVolt: number;
      powerDrawFraction: number;
      utilization: number;
    };
    cycle: {
      decision: 'PROMOTE' | 'RETRACT' | 'MAINTAIN' | 'QUARANTINE';
      headroomC: number;
      loadFactor: number;
      transitions: { kind: string; reason: string }[];
    };
    governor: {
      state: {
        currentFrequencyMhz: number;
        currentVoltageV: number;
        lastDecision: 'PROMOTE' | 'RETRACT' | 'MAINTAIN' | 'QUARANTINE';
      };
      recentEvents: { kind: string; timestamp: string }[];
      previousState?: {
        currentFrequencyMhz: number;
        currentVoltageV: number;
        lastDecision: 'PROMOTE' | 'RETRACT' | 'MAINTAIN' | 'QUARANTINE';
      };
    };
    thermalBridge?: {
      source: 'env' | 'file' | 'system';
      sourceDetail: string;
      vendor: string;
      deviceFamily: string;
      observedAtMs: number;
      healthy: boolean;
      sensors: { name: string; temperatureC: number; fanRpm: number; voltageV: number; powerWatts: number; status: 'ok' | 'warn' | 'critical' }[];
      summary: { hottestSensor: string; hottestTemperatureC: number; averageTemperatureC: number; alertCount: number };
    };
  };
  sovereignxClusterRouting?: {
    clusterDecision: {
      action: 'dispatch' | 'delay' | 'drop';
      nodeId: string | null;
      nodeRole: 'CPU' | 'GPU' | 'MIXED' | null;
      backend: string;
      reason: string;
    };
    selectedNode: {
      nodeId: string;
      role: 'CPU' | 'GPU' | 'MIXED';
      region: string;
      maxJobs: number;
      activeJobs: number;
      cpuUtilization: number;
      gpuUtilization: number;
      gpuTempC: number;
      lastHeartbeatAtMs: number;
      health: 'healthy' | 'degraded' | 'quarantined';
      preferredBackend?: string;
    } | null;
    alternateNodes: {
      nodeId: string;
      role: 'CPU' | 'GPU' | 'MIXED';
      eligible: boolean;
      score: number;
      reasons: string[];
    }[];
    nodeScores: {
      nodeId: string;
      role: 'CPU' | 'GPU' | 'MIXED';
      eligible: boolean;
      score: number;
      reasons: string[];
    }[];
    summary: {
      nodeCount: number;
      healthyNodeCount: number;
      eligibleNodeCount: number;
      selectionPolicy: string;
    };
  };
  sovereignxClusterGovernance?: {
    available: boolean;
    controlState: {
      desiredNodeCount: number;
      quarantinedNodeIds: string[];
      preferredFailoverNodeId: string | null;
      lastAction: {
        action: 'steady_state' | 'quarantine' | 'restore' | 'scale_up' | 'scale_down' | 'failover';
        nodeId: string | null;
        desiredNodeCount: number;
        reason: string;
        observedAtMs: number;
      } | null;
    };
    membershipNodes: {
      nodeId: string;
      role: 'CPU' | 'GPU' | 'MIXED';
      region: string;
      health: 'healthy' | 'degraded' | 'quarantined';
      controlState: 'active' | 'standby' | 'quarantined';
      controlReason: string;
      failoverCandidate: boolean;
      preferredBackend?: string;
    }[];
    summary: {
      nodeCount: number;
      healthyNodeCount: number;
      eligibleNodeCount: number;
      activeNodeCount: number;
      quarantinedNodeCount: number;
      standbyNodeCount: number;
      desiredNodeCount: number;
      selectionPolicy: string;
    };
    autoscaling: {
      action: 'scale_up' | 'scale_down' | 'hold';
      desiredNodeCount: number;
      recommendedNodeCount: number;
      activeNodeCount: number;
      eligibleNodeCount: number;
      pressureScore: number;
      reason: string;
    };
    failover: {
      action: 'failover' | 'hold';
      fromNodeId: string | null;
      toNodeId: string | null;
      trigger: string;
      reason: string;
      standbyNodeIds: string[];
    };
    soakChaosValidation: {
      available: boolean;
      soakRuns: number;
      stableSelections: number;
      chaosRuns: number;
      chaosQuarantines: number;
      failovers: number;
      autoscalingTriggers: number;
      passed: boolean;
      rows: {
        iteration: number;
        scenario: string;
        selectedNodeId: string | null;
        clusterAction: string;
        failoverAction: string;
        autoscalingAction: string;
        quarantinedNodeIds: string[];
        stableSelection: boolean;
      }[];
    };
    traceabilityMatrix: {
      available: boolean;
      source: string;
      rows: {
        capabilityId: string;
        capabilityName: string;
        constitutionalRequirements: string[];
        architecturalComponent: string;
        evidenceIds: string[];
        tests: string[];
        proofSurfaceIds: string[];
        status: string;
      }[];
      summary: {
        capabilityCount: number;
        requirementCount: number;
        evidenceCount: number;
        testCount: number;
        proofSurfaceCount: number;
      };
    };
  };
  thermalBridge?: {
    source: 'env' | 'file' | 'system';
    sourceDetail: string;
    vendor: string;
    deviceFamily: string;
    observedAtMs: number;
    healthy: boolean;
    sensors: { name: string; temperatureC: number; fanRpm: number; voltageV: number; powerWatts: number; status: 'ok' | 'warn' | 'critical' }[];
    summary: { hottestSensor: string; hottestTemperatureC: number; averageTemperatureC: number; alertCount: number };
  };
  constitutionalTraceability?: {
    available: boolean;
    source: string;
    rows: {
      capabilityId: string;
      capabilityName: string;
      constitutionalRequirements: string[];
      architecturalComponent: string;
      evidenceIds: string[];
      tests: string[];
      proofSurfaceIds: string[];
      status: string;
    }[];
    summary: {
      capabilityCount: number;
      requirementCount: number;
      evidenceCount: number;
      testCount: number;
      proofSurfaceCount: number;
    };
  };
  overrideDrill?: {
    available: boolean;
    authority: string;
    requestedDecision: 'PROMOTE' | 'RETRACT' | 'MAINTAIN' | 'QUARANTINE';
    baselineDecision: 'PROMOTE' | 'RETRACT' | 'MAINTAIN' | 'QUARANTINE';
    accepted: boolean;
    reason: string;
    driftFromBaseline: boolean;
    replayable: true;
    previewState: {
      currentFrequencyMhz: number;
      currentVoltageV: number;
      lastDecision: 'PROMOTE' | 'RETRACT' | 'MAINTAIN' | 'QUARANTINE';
    };
    guardrails: string[];
  };
  replayValidation?: {
    available: boolean;
    storePath: string;
    recordCount: number;
    baselineMatches: number;
    baselineMismatches: number;
    chaosRuns: number;
    chaosQuarantines: number;
    passed: boolean;
    rows: { sequence: number; recordedAt: string; baselineDecision: string; replayDecision: string; decisionMatched: boolean; stateMatched: boolean; chaosDecisions: { kind: string; decision: string; quarantined: boolean }[] }[];
  };
  hardwareBenchmarks?: {
    available: boolean;
    generatedAtMs: number;
    source: string;
    sourceDetail: string;
    currentDecision: string;
    baselineScenario: {
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
    governedScenario: {
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
    counterfactualScenarios: {
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
    }[];
    comparisons: {
      metric: string;
      baseline: number;
      governed: number;
      delta: number;
      deltaPct: number;
    }[];
    summary: {
      estimatedLatencyReductionPct: number;
      estimatedThroughputGainPct: number;
      estimatedCostEfficiencyGainPct: number;
      thermalHeadroomDeltaC: number;
      recommendation: string;
    };
  };
  hardwareReplayStore?: {
    available: boolean;
    storePath: string;
    entryCount: number;
    latest: {
      sequence: number;
      recordedAt: string;
      source: string;
      sourceDetail: string;
      decision: 'PROMOTE' | 'RETRACT' | 'MAINTAIN' | 'QUARANTINE';
    } | null;
    recentRecords: {
      sequence: number;
      recordedAt: string;
      source: string;
      sourceDetail: string;
      decision: 'PROMOTE' | 'RETRACT' | 'MAINTAIN' | 'QUARANTINE';
    }[];
  };
  proofSurfaces?: ProofSurfaceSummary[];
  aais?: {
    connected: boolean;
    baseUrl: string;
    status: string;
    service: string;
    activeModelMode: string;
    aiStatus: string;
    aiBootstrapStatus: string;
    mockModeActive: boolean;
    legacyApiLoaded: boolean;
    contractors: unknown[];
    error?: string;
  };
  cab?: {
    available: boolean;
    entryCount: number;
    activeCount: number;
    invariants: { passed: boolean; results: { invariantId: string; status: string; detail: string }[] };
    latest: {
      intents: string[];
      decisions: string[];
      evidenceChains: string[];
      continuityReceipts: string[];
      reconstructionPlans: string[];
    };
  };
  pricing?: {
    available: boolean;
    storePath: string;
    entryCount: number;
    totalRevenueUsd: number;
    totalCostUsd: number;
    totalGrossMarginUsd: number;
    grossMarginPct: number;
    recentEntries: {
      requestId: string;
      recordedAt: string;
      segment: string;
      strategy: string;
      routedRequests: number;
      monthlyCustomers: number;
      estimatedRevenueUsd: number;
      estimatedCostUsd: number;
      estimatedGrossMarginUsd: number;
      estimatedGrossMarginPct: number;
      selectedModel: string;
      backend: string;
      routeReason: string;
    }[];
    bySegment: {
      segment: string;
      entryCount: number;
      revenueUsd: number;
      costUsd: number;
      grossMarginUsd: number;
      grossMarginPct: number;
    }[];
    byStrategy: {
      strategy: string;
      entryCount: number;
      revenueUsd: number;
      costUsd: number;
      grossMarginUsd: number;
      grossMarginPct: number;
    }[];
    cohortHistory: {
      cohort: string;
      entryCount: number;
      revenueUsd: number;
      costUsd: number;
      grossMarginUsd: number;
      grossMarginPct: number;
      strategyMix: string[];
    }[];
  };
  evidenceGraph?: ConstitutionalEvidenceGraphSummary;
};

type ScoreVector = {
  continuity: number;
  governance: number;
  memory: number;
  coordination: number;
  confidence: number;
};

type MriV2Response = {
  state_vector: ScoreVector;
  delta_state: ScoreVector;
  trajectory_vector: {
    continuity: number;
    governance: number;
    memory: number;
    coordination: number;
    magnitude: number;
    confidenceWeightedMagnitude: number;
    confidence_weighted_magnitude: number;
  };
  benchmarks: {
    industryAverage: ScoreVector;
    topQuartile: ScoreVector;
    previousMeasurement: ScoreVector;
    summary: string;
    deltas: { dimension: keyof ScoreVector; vsPrevious: number; vsIndustry: number; vsTopQuartile: number }[];
    bar_markers: Record<keyof ScoreVector, { current: number; previous: number; industry: number; topQuartile: number }>;
  };
  trajectory_signatures: string[];
  trajectory_breakdown: { dimension: keyof ScoreVector; delta: number; confidence: number; contribution: number; direction: string }[];
  projection: ScoreVector[];
  risks: { id: string; type: string; description: string }[];
  interventions: { id: string; type: string; description: string; score: number }[];
  evidence: { beforeConfidence: number; afterConfidence: number; meanConfidence: number; confidenceTensor: Record<string, number> };
  before_after: { before: ScoreVector; after: ScoreVector };
};

type EnforcementSummary = {
  status: string;
  events: { receiptId: string; verdict: string; reasonCode: string; transitionId?: string }[];
  invariantSet?: { active: number; disabled: number };
  tokenCounts?: Record<string, number>;
  enforcementRatePerMinute?: number;
  replayAttemptsBlocked?: number;
};

type MetaSummary = {
  podId: string;
  generativeCoreId: string;
  metaInvariantCount: number;
};

type CustomerRegistry = {
  customers: {
    id: string;
    email: string;
    planId: string;
    planName: string;
    entitlements: {
      routingTier: string;
      codexPacketHandoff: boolean;
      usageLedger: boolean;
      marginDashboard: boolean;
      auditScope: string;
    };
    createdAt: string;
  }[];
  customerCount: number;
  planCounts: Record<string, number>;
};

type OrganizationRegistry = {
  organizations: {
    id: string;
    name: string;
    ownerCustomerId: string;
    billingContactEmail: string;
    domain?: string;
    members: { customerId: string; role: string; joinedAt: string }[];
    createdAt: string;
    updatedAt: string;
  }[];
  organizationCount: number;
  roleCounts: Record<string, number>;
};

type CustomerQuotaDashboard = {
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
  quota: {
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
  usageRecords: { operation: string; units: number; timestamp: string }[];
};

type OrganizationUsageDashboard = {
  organizationId: string;
  total: number;
  byKind: Record<string, number>;
  summary: {
    total: number;
    byKind: Record<string, number>;
  };
  overageEvents: {
    id: string;
    kind: string;
    amount: number;
    occurredAt: string;
    metadata?: Record<string, unknown>;
  }[];
};

type OrganizationAuditDashboard = {
  organizationId: string;
  pricing: unknown[];
  routing: unknown[];
  entitlements: unknown[];
};

type CepArtifactKind = 'promotion-request' | 'replay-job' | 'decision';

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

type CepArtifactFilters = {
  trustBand: CepTrustBand | null;
  minTrustScore: number | null;
  governanceLevel: CepTrustGovernanceLevel | null;
  includeUntrusted: boolean;
};

type CepArtifactRecord = {
  id: string;
  kind: CepArtifactKind;
  title: string;
  source: string;
  relatedArtifactId?: string;
  recordedAt: string;
  payload: unknown;
  trust?: CepTrustPacket | null;
  trustPolicy?: CepTrustPolicy | null;
};

type CepArtifactExport = {
  storePath: string;
  entryCount: number;
  countsByKind: Record<CepArtifactKind, number>;
  records: CepArtifactRecord[];
  recentRecords: CepArtifactRecord[];
  trustFilters?: CepArtifactFilters;
  trustSummary?: CepTrustSummary;
  viewState: {
    selectedKind: CepArtifactKind;
    selectedArtifactId: string | null;
    updatedAt: string;
    source: 'local' | 'remote';
  };
};

type TreasuryScheduleResponse = {
  schedule: {
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

type LoadedState = {
  telemetry: TelemetryResponse;
  hardwareConsole: HardwareConsoleSummary | null;
  mriV2: MriV2Response;
  enforcement: EnforcementSummary;
  meta: MetaSummary;
  customers: CustomerRegistry;
  organizations: OrganizationRegistry;
  quota: CustomerQuotaDashboard | null;
  organizationUsage: OrganizationUsageDashboard | null;
  organizationAudit: OrganizationAuditDashboard | null;
  cepArtifacts: CepArtifactExport;
  treasurySchedule: TreasuryScheduleResponse;
  governanceEvolution: GovernanceEvolutionTimeline;
  coriAlpha: CoriAlphaWorkspaceSummary | null;
};

type GovernanceEvolutionTimeline = {
  timelineId: string;
  entries: GovernanceEvolutionEntry[];
  summary: {
    entryCount: number;
    continuityReports: number;
    governanceDiffs: number;
    replayReports: number;
    validatedAmendments: number;
  };
};

type GovernanceEvolutionEntry = {
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
    mode: string;
    decision: string;
    stage: string;
    summary: string;
    receiptId: string;
    lawOfLawsEntryId: string;
  };
};

type ProofSurfaceCatalogState = {
  status: 'loading' | 'loaded' | 'error';
  catalogUrl: string;
  error?: string;
  proofSurfaces: ProofSurfaceSummary[];
};

export const App: React.FC = () => {
  const [state, setState] = useState<LoadedState | null>(null);
  const [selectedCepArtifactId, setSelectedCepArtifactId] = useState<string | null>(null);
  const [selectedGovernanceEvolutionId, setSelectedGovernanceEvolutionId] = useState<string | null>(null);
  const [cepTrustBandFilter] = useState<CepTrustBand | 'all'>('all');
  const [cepTrustGovernanceFilter] = useState<CepTrustGovernanceLevel | 'all'>('all');
  const [cepTrustMinScoreFilter] = useState<string>('');
  const [hardwareRefreshNonce, setHardwareRefreshNonce] = useState(0);
  const [proofSurfaceCatalog, setProofSurfaceCatalog] = useState<ProofSurfaceCatalogState>(() => {
    const initialCatalogUrl = resolveInitialProofSurfaceCatalogUrl(
      typeof window === 'undefined' ? '' : window.location.search,
      typeof window === 'undefined' ? null : window.localStorage.getItem(PROOF_SURFACE_CATALOG_STORAGE_KEY),
    );
    return {
      status: 'loading',
      catalogUrl: initialCatalogUrl,
      proofSurfaces: [],
    };
  });
  const [catalogUrlInput, setCatalogUrlInput] = useState(proofSurfaceCatalog.catalogUrl);
  const [selectedProofSurfaceId, setSelectedProofSurfaceId] = useState<string | null>(null);
  const [arenaMode, setArenaMode] = useState<ArenaSnapshot>(() => createArenaModeSnapshot());
  const cepArtifactQuery = useMemo(() => {
    const params = new URLSearchParams();
    if (cepTrustBandFilter !== 'all') {
      params.set('trustBand', cepTrustBandFilter);
    }
    if (cepTrustGovernanceFilter !== 'all') {
      params.set('governanceLevel', cepTrustGovernanceFilter);
    }
    const parsedMinScore = Number(cepTrustMinScoreFilter);
    if (cepTrustMinScoreFilter.trim() && Number.isFinite(parsedMinScore)) {
      params.set('minTrustScore', String(parsedMinScore));
    }
    return params.toString();
  }, [cepTrustBandFilter, cepTrustGovernanceFilter, cepTrustMinScoreFilter]);

  useEffect(() => {
    const fetchTelemetry = async () => {
      const cepArtifactsUrl = cepArtifactQuery ? `/cep/artifacts/export.json?${cepArtifactQuery}` : '/cep/artifacts/export.json';
      const [telemetryRes, hardwareSummaryRes, mriRes, enforcementRes, metaRes, customersRes, organizationsRes, quotaRes, treasuryScheduleRes, cepArtifactsRes, governanceEvolutionRes, coriAlphaRes] = await Promise.all([
        fetch('/telemetry'),
        fetch('/hardware/summary'),
        fetch('/mri/v2'),
        fetch('/cen/events'),
        fetch('/pod/meta_constitutional_collapse'),
        fetch('/customers'),
        fetch('/organizations'),
        fetch('/customers/quota'),
        fetch('/treasury/schedule'),
        fetch(cepArtifactsUrl),
        fetch('/evolution/timeline'),
        fetch('/cori-alpha/summary'),
      ]);
      const telemetry = (await telemetryRes.json()) as TelemetryResponse;
      const hardwareConsole = hardwareSummaryRes.ok ? ((await hardwareSummaryRes.json()) as HardwareConsoleSummary) : null;
      const mriV2 = (await mriRes.json()) as MriV2Response;
      const enforcement = (await enforcementRes.json()) as EnforcementSummary;
      const metaPayload = (await metaRes.json()) as {
        pod: { podId: string };
        collapse: { generativeCoreId: string; metaInvariants: unknown[] };
      };
      const customers = (await customersRes.json()) as CustomerRegistry;
      const organizations = (await organizationsRes.json()) as OrganizationRegistry;
      const quota = quotaRes.ok ? ((await quotaRes.json()) as CustomerQuotaDashboard) : null;
      const treasurySchedule = (await treasuryScheduleRes.json()) as TreasuryScheduleResponse;
      const cepArtifacts = (await cepArtifactsRes.json()) as CepArtifactExport;
      const governanceEvolution = (await governanceEvolutionRes.json()) as GovernanceEvolutionTimeline;
      const coriAlphaPayload = (await coriAlphaRes.json().catch(() => null)) as { surface?: CoriAlphaWorkspaceSummary } | null;
      const activeOrganizationId = quota?.customer?.organizationId ?? organizations.organizations[0]?.id ?? null;
      let organizationUsage: OrganizationUsageDashboard | null = null;
      let organizationAudit: OrganizationAuditDashboard | null = null;
      if (activeOrganizationId) {
        const [organizationUsageRes, organizationAuditRes] = await Promise.all([
          fetch(`/organizations/${encodeURIComponent(activeOrganizationId)}/usage`),
          fetch(`/organizations/${encodeURIComponent(activeOrganizationId)}/audit`),
        ]);
        if (organizationUsageRes.ok) {
          organizationUsage = (await organizationUsageRes.json()) as OrganizationUsageDashboard;
        }
        if (organizationAuditRes.ok) {
          organizationAudit = (await organizationAuditRes.json()) as OrganizationAuditDashboard;
        }
      }
      setState({
        telemetry,
        hardwareConsole,
        mriV2,
        enforcement,
        meta: {
          podId: metaPayload.pod.podId,
          generativeCoreId: metaPayload.collapse.generativeCoreId,
          metaInvariantCount: metaPayload.collapse.metaInvariants.length,
        },
        customers,
        organizations,
        quota,
        organizationUsage,
        organizationAudit,
        cepArtifacts,
        treasurySchedule,
        governanceEvolution,
        coriAlpha: coriAlphaRes.ok ? (coriAlphaPayload?.surface ?? null) : null,
      });
    };
    fetchTelemetry();
    const id = setInterval(fetchTelemetry, 5000);
    return () => clearInterval(id);
  }, [cepArtifactQuery, hardwareRefreshNonce]);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof EventSource === 'undefined') {
      return;
    }

    const source = new EventSource('/hardware/stream');
    const updateFromStream = (event: MessageEvent<string>) => {
      try {
        const hardwareConsole = JSON.parse(event.data) as HardwareConsoleSummary;
        setState((current) => (current ? { ...current, hardwareConsole } : current));
      } catch {
        // Ignore malformed stream events and keep polling as the fallback.
      }
    };

    source.addEventListener('summary', updateFromStream as EventListener);
    source.onmessage = updateFromStream;

    return () => {
      source.close();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const fetchArena = async () => {
      try {
        const response = await fetch('/arena');
        if (!response.ok) {
          return;
        }
        const arena = (await response.json()) as ArenaSnapshot;
        if (!cancelled) {
          setArenaMode(arena);
        }
      } catch {
        // Fall back to the seeded local arena snapshot.
      }
    };

    void fetchArena();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const loadCatalog = async () => {
      setProofSurfaceCatalog((current) => ({
        ...current,
        status: 'loading',
        error: undefined,
      }));

      try {
        const proofRes = await fetch(proofSurfaceCatalog.catalogUrl, {
          headers: {
            accept: 'application/json',
          },
        });

        if (!proofRes.ok) {
          throw new Error(`catalog request failed with ${proofRes.status}`);
        }

        const proofPayload = (await proofRes.json()) as {
          summaries?: ProofSurfaceSummary[];
          catalog?: { surfaces?: Array<{ surface?: unknown }> };
        };
        const summaries = Array.isArray(proofPayload.summaries)
          ? proofPayload.summaries
          : Array.isArray(proofPayload.catalog?.surfaces)
            ? proofPayload.catalog.surfaces
                .map((entry) => entry.surface)
                .filter(isProofSurfaceSummary)
            : [];

        if (!cancelled) {
          setProofSurfaceCatalog({
            status: 'loaded',
            catalogUrl: proofSurfaceCatalog.catalogUrl,
            proofSurfaces: summaries,
          });
        }
      } catch (error) {
        if (!cancelled) {
          setProofSurfaceCatalog({
            status: 'error',
            catalogUrl: proofSurfaceCatalog.catalogUrl,
            error: error instanceof Error ? error.message : String(error),
            proofSurfaces: [],
          });
        }
      }
    };

    void loadCatalog();
    return () => {
      cancelled = true;
    };
  }, [proofSurfaceCatalog.catalogUrl]);

  useEffect(() => {
    if (proofSurfaceCatalog.status !== 'loaded' || proofSurfaceCatalog.proofSurfaces.length === 0) {
      return;
    }

    const selectedSurfaceStillExists = selectedProofSurfaceId
      ? proofSurfaceCatalog.proofSurfaces.some((surface) => surface.identity.id === selectedProofSurfaceId)
      : false;

    if (!selectedSurfaceStillExists) {
      setSelectedProofSurfaceId(proofSurfaceCatalog.proofSurfaces[0].identity.id);
    }
  }, [proofSurfaceCatalog.proofSurfaces, proofSurfaceCatalog.status, selectedProofSurfaceId]);

  useEffect(() => {
    if (!state?.cepArtifacts.viewState.selectedArtifactId) {
      return;
    }
    setSelectedCepArtifactId(state.cepArtifacts.viewState.selectedArtifactId);
  }, [state?.cepArtifacts.viewState.selectedArtifactId]);

  useEffect(() => {
    const entries = state?.governanceEvolution.entries ?? [];
    const firstEntryId = entries[0]?.eventId ?? null;
    if (!firstEntryId) {
      return;
    }
    setSelectedGovernanceEvolutionId((current) => {
      if (current && entries.some((entry) => entry.eventId === current)) {
        return current;
      }
      return firstEntryId;
    });
  }, [state?.governanceEvolution.entries]);

  const applyCatalogUrl = (nextCatalogUrl: string) => {
    const normalizedCatalogUrl = normalizeProofSurfaceCatalogUrl(nextCatalogUrl);
    setCatalogUrlInput(normalizedCatalogUrl);
    setProofSurfaceCatalog((current) => ({
      ...current,
      status: 'loading',
      catalogUrl: normalizedCatalogUrl,
      error: undefined,
      proofSurfaces: current.status === 'loaded' ? current.proofSurfaces : [],
    }));

    if (typeof window !== 'undefined') {
      window.localStorage.setItem(PROOF_SURFACE_CATALOG_STORAGE_KEY, normalizedCatalogUrl);
      const nextLocation = new URL(window.location.href);
      nextLocation.searchParams.set('catalogUrl', normalizedCatalogUrl);
      window.history.replaceState({}, '', `${nextLocation.pathname}${nextLocation.search}${nextLocation.hash}`);
    }
  };

  const handleCatalogSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    applyCatalogUrl(catalogUrlInput);
  };

  const resetCatalogUrl = () => {
    applyCatalogUrl(DEFAULT_PROOF_SURFACE_CATALOG_URL);
  };

  const useCatalogFromQuery = () => {
    applyCatalogUrl(resolveInitialProofSurfaceCatalogUrl(window.location.search, null));
  };

  if (!state) return <div>Loading telemetry...</div>;
  return (
    <OpsConsoleShell
      telemetry={state.telemetry}
      hardwareConsole={state.hardwareConsole}
      mriV2={state.mriV2}
      enforcement={state.enforcement}
      meta={state.meta}
      customers={state.customers}
      organizations={state.organizations}
      quota={state.quota}
      organizationUsage={state.organizationUsage}
      organizationAudit={state.organizationAudit}
      cepArtifacts={state.cepArtifacts}
      treasurySchedule={state.treasurySchedule}
      governanceEvolution={state.governanceEvolution}
      coriAlpha={state.coriAlpha}
      proofSurfaceCatalog={proofSurfaceCatalog}
      catalogUrlInput={catalogUrlInput}
      selectedProofSurfaceId={selectedProofSurfaceId}
      onCatalogUrlInputChange={setCatalogUrlInput}
      onCatalogSubmit={handleCatalogSubmit}
      onResetCatalogUrl={resetCatalogUrl}
      onUseQueryCatalogUrl={useCatalogFromQuery}
      onSelectedProofSurfaceChange={setSelectedProofSurfaceId}
      selectedCepArtifactId={selectedCepArtifactId}
      onSelectedCepArtifactIdChange={setSelectedCepArtifactId}
      selectedGovernanceEvolutionId={selectedGovernanceEvolutionId}
      onSelectedGovernanceEvolutionIdChange={setSelectedGovernanceEvolutionId}
      onHardwareRefreshRequested={() => setHardwareRefreshNonce((value) => value + 1)}
      arenaMode={arenaMode}
    />
  );
};

type OpsConsoleShellProps = LoadedState & {
  proofSurfaceCatalog: ProofSurfaceCatalogState;
  catalogUrlInput: string;
  selectedProofSurfaceId: string | null;
  selectedGovernanceEvolutionId: string | null;
  onCatalogUrlInputChange: (value: string) => void;
  onCatalogSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onResetCatalogUrl: () => void;
  onUseQueryCatalogUrl: () => void;
  onSelectedProofSurfaceChange: (value: string) => void;
  selectedCepArtifactId: string | null;
  onSelectedCepArtifactIdChange: (value: string) => void;
  onSelectedGovernanceEvolutionIdChange: (value: string) => void;
  onHardwareRefreshRequested: () => void;
  cepTrustBandFilter?: CepTrustBand | 'all';
  cepTrustGovernanceFilter?: CepTrustGovernanceLevel | 'all';
  cepTrustMinScoreFilter?: string;
  onCepTrustBandFilterChange?: (value: CepTrustBand | 'all') => void;
  onCepTrustGovernanceFilterChange?: (value: CepTrustGovernanceLevel | 'all') => void;
  onCepTrustMinScoreFilterChange?: (value: string) => void;
  arenaMode: ArenaSnapshot;
};

export const OpsConsoleShell: React.FC<OpsConsoleShellProps> = ({
  telemetry,
  hardwareConsole: hardwareConsoleSnapshot,
  mriV2,
  enforcement,
  meta,
  customers,
  organizations,
  quota,
  organizationUsage,
  organizationAudit,
  cepArtifacts,
  treasurySchedule,
  governanceEvolution,
  coriAlpha,
  proofSurfaceCatalog,
  catalogUrlInput,
  selectedProofSurfaceId,
  selectedGovernanceEvolutionId,
  onCatalogUrlInputChange,
  onCatalogSubmit,
  onResetCatalogUrl,
  onUseQueryCatalogUrl,
  onSelectedProofSurfaceChange,
  selectedCepArtifactId,
  onSelectedCepArtifactIdChange,
  onSelectedGovernanceEvolutionIdChange,
  onHardwareRefreshRequested,
  cepTrustBandFilter = 'all',
  cepTrustGovernanceFilter = 'all',
  cepTrustMinScoreFilter = '',
  onCepTrustBandFilterChange = () => {},
  onCepTrustGovernanceFilterChange = () => {},
  onCepTrustMinScoreFilterChange = () => {},
  arenaMode,
}) => (
  <div style={{ fontFamily: 'system-ui', padding: 16, color: '#172026', background: '#f6f7f9' }}>
    <h1 style={{ margin: '0 0 16px' }}>AAES-OS Ops Console</h1>
      <nav style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
        <a href="#catalog">Constitutional Knowledge Graph</a>
        <a href="#mri">MRI Cockpit</a>
        <a href="#enforcement">Enforcement Dashboard</a>
        <a href="#meta">Meta-Constitutional Console</a>
        <a href="#arena">Arena Mode</a>
        <a href="#hardware-console">Hardware Console</a>
        <a href="#cluster">Cluster Governance</a>
        <a href="#aais">AAIS Runtime</a>
        <a href="#cab">CAB Continuity</a>
        <a href="#cori-alpha">CORI Alpha</a>
        <a href="#governance-evolution">Governance Evolution</a>
        <a href="#org-usage">Org Usage</a>
        <a href="#treasury">Treasury Schedule</a>
      </nav>

    <section id="catalog" style={sectionStyle}>
      <h2>Constitutional Knowledge Graph</h2>
      <p>Point the Ops Console at any proof-surface backend and explore surfaces by domain, health, and constitutional profile.</p>
      <form onSubmit={onCatalogSubmit} style={{ display: 'grid', gap: 12, marginBottom: 12 }}>
        <label style={{ display: 'grid', gap: 6 }}>
          <span style={{ fontSize: 13, fontWeight: 600 }}>Catalog URL</span>
          <input
            value={catalogUrlInput}
            onChange={(event) => onCatalogUrlInputChange(event.target.value)}
            spellCheck={false}
            placeholder={DEFAULT_PROOF_SURFACE_CATALOG_URL}
            style={{
              border: '1px solid #b8c2cf',
              borderRadius: 10,
              padding: '10px 12px',
              fontSize: 14,
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
            }}
          />
        </label>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          <button type="submit" style={buttonStyle}>Load catalog</button>
          <button type="button" onClick={onUseQueryCatalogUrl} style={secondaryButtonStyle}>Use URL from query</button>
          <button type="button" onClick={onResetCatalogUrl} style={secondaryButtonStyle}>Reset to default</button>
        </div>
      </form>
      <div style={{ color: '#5f6b7a', fontSize: 13, display: 'grid', gap: 4, marginBottom: 12 }}>
        <div>Active catalog: {proofSurfaceCatalog.catalogUrl}</div>
        <div>Status: {proofSurfaceCatalog.status}</div>
        {proofSurfaceCatalog.error ? <div>Error: {proofSurfaceCatalog.error}</div> : null}
      </div>
      <TraceabilityMatrixCallout surfaces={proofSurfaceCatalog.proofSurfaces} />
      <ProofSurfaceKnowledgeGraph
        surfaces={proofSurfaceCatalog.proofSurfaces}
        selectedProofSurfaceId={selectedProofSurfaceId}
        onSelectedProofSurfaceChange={onSelectedProofSurfaceChange}
      />
    </section>

    <ConstitutionalEvidenceGraphPanel evidenceGraph={telemetry.evidenceGraph} />

    <OpsConsoleView
      telemetry={telemetry}
      hardwareConsole={hardwareConsoleSnapshot}
      mriV2={mriV2}
      enforcement={enforcement}
      meta={meta}
      customers={customers}
      organizations={organizations}
      quota={quota}
      organizationUsage={organizationUsage}
      organizationAudit={organizationAudit}
      cepArtifacts={cepArtifacts}
      treasurySchedule={treasurySchedule}
      governanceEvolution={governanceEvolution}
      coriAlpha={coriAlpha}
      arenaMode={arenaMode}
      selectedCepArtifactId={selectedCepArtifactId}
      onSelectedCepArtifactIdChange={onSelectedCepArtifactIdChange}
      selectedGovernanceEvolutionId={selectedGovernanceEvolutionId}
      onSelectedGovernanceEvolutionIdChange={onSelectedGovernanceEvolutionIdChange}
      onHardwareRefreshRequested={onHardwareRefreshRequested}
      cepTrustBandFilter={cepTrustBandFilter}
      cepTrustGovernanceFilter={cepTrustGovernanceFilter}
      cepTrustMinScoreFilter={cepTrustMinScoreFilter}
      onCepTrustBandFilterChange={onCepTrustBandFilterChange}
      onCepTrustGovernanceFilterChange={onCepTrustGovernanceFilterChange}
      onCepTrustMinScoreFilterChange={onCepTrustMinScoreFilterChange}
    />
  </div>
);

export const OpsConsoleView: React.FC<
  LoadedState & {
    arenaMode: ArenaSnapshot;
    selectedCepArtifactId: string | null;
    onSelectedCepArtifactIdChange: (value: string) => void;
    governanceEvolution: GovernanceEvolutionTimeline;
    coriAlpha: CoriAlphaWorkspaceSummary | null;
    selectedGovernanceEvolutionId: string | null;
    onSelectedGovernanceEvolutionIdChange: (value: string) => void;
    onHardwareRefreshRequested: () => void;
    cepTrustBandFilter: CepTrustBand | 'all';
    cepTrustGovernanceFilter: CepTrustGovernanceLevel | 'all';
    cepTrustMinScoreFilter: string;
    onCepTrustBandFilterChange: (value: CepTrustBand | 'all') => void;
    onCepTrustGovernanceFilterChange: (value: CepTrustGovernanceLevel | 'all') => void;
    onCepTrustMinScoreFilterChange: (value: string) => void;
  }
> = ({
  telemetry,
  hardwareConsole: hardwareConsoleSnapshot,
  mriV2,
  enforcement,
  meta,
  customers,
  organizations,
  quota,
  organizationUsage,
  organizationAudit,
  cepArtifacts,
  treasurySchedule,
  governanceEvolution,
  coriAlpha,
  arenaMode,
  selectedCepArtifactId,
  onSelectedCepArtifactIdChange,
  selectedGovernanceEvolutionId,
  onSelectedGovernanceEvolutionIdChange,
  onHardwareRefreshRequested,
  cepTrustBandFilter,
  cepTrustGovernanceFilter,
  cepTrustMinScoreFilter,
  onCepTrustBandFilterChange,
  onCepTrustGovernanceFilterChange,
  onCepTrustMinScoreFilterChange,
}) => {
  return (
  <div>
    <section id="mri" style={sectionStyle}>
      <h2>MRI Cockpit</h2>
      <p>{mriV2.benchmarks.summary}</p>
      <div style={gridStyle}>
        {(['continuity', 'governance', 'memory', 'coordination', 'confidence'] as const).map((dimension) => (
          <BenchmarkCard
            key={dimension}
            label={dimension}
            score={mriV2.state_vector[dimension]}
            delta={mriV2.delta_state[dimension]}
            markers={mriV2.benchmarks.bar_markers[dimension]}
          />
        ))}
      </div>
      <div style={gridStyle}>
        <Panel title="Risk Register">
          <ul>{mriV2.risks.map((risk) => <li key={risk.id}>{risk.type}: {risk.description}</li>)}</ul>
        </Panel>
        <Panel title="Intervention Ranking">
          <ol>{mriV2.interventions.slice(0, 3).map((item) => <li key={item.id}>{item.type} ({item.score})</li>)}</ol>
        </Panel>
        <Panel title="Trajectory">
          <p>Magnitude {mriV2.trajectory_vector.magnitude.toFixed(3)}</p>
          <p>Weighted {mriV2.trajectory_vector.confidence_weighted_magnitude.toFixed(3)}</p>
          <p>{mriV2.trajectory_signatures.join(', ')}</p>
        </Panel>
        <Panel title="Evidence Ledger">
          <p>Mean confidence {mriV2.evidence.meanConfidence.toFixed(3)}</p>
          <p>Before {mriV2.evidence.beforeConfidence} | After {mriV2.evidence.afterConfidence}</p>
        </Panel>
        <Panel title="Evidence Graph">
          <p>Root receipt {telemetry.evidenceGraph?.rootReceiptId ?? 'loading'}</p>
          <p>Verified claims {telemetry.evidenceGraph?.verifiedClaimCount ?? 0}</p>
          <p>Views {telemetry.evidenceGraph?.viewCount ?? 0}</p>
        </Panel>
      </div>
    </section>

    <section id="enforcement" style={sectionStyle}>
      <h2>Enforcement Dashboard</h2>
      <div style={gridStyle}>
        <Metric label="CEN" value={enforcement.status} />
        <Metric label="Invariant Set" value={`${enforcement.invariantSet?.active ?? 0} active`} />
        <Metric label="Rate" value={`${enforcement.enforcementRatePerMinute ?? 0}/min`} />
        <Metric label="Replay Blocks" value={String(enforcement.replayAttemptsBlocked ?? 0)} />
      </div>
      <table>
        <thead><tr><th>Receipt</th><th>Verdict</th><th>Reason</th></tr></thead>
        <tbody>
          {enforcement.events.map((event) => (
            <tr key={event.receiptId}><td>{event.receiptId}</td><td>{event.verdict}</td><td>{event.reasonCode}</td></tr>
          ))}
        </tbody>
      </table>
    </section>

    <section id="meta" style={sectionStyle}>
      <h2>Meta-Constitutional Console</h2>
      <div style={gridStyle}>
        <Metric label="POD" value={meta.podId} />
        <Metric label="Core" value={meta.generativeCoreId} />
        <Metric label="Meta-Invariants" value={String(meta.metaInvariantCount)} />
        <Metric label="Drift" value={telemetry.drift.score.toFixed(3)} />
      </div>
      </section>

      <HardwareConsolePage
        hardwareConsole={hardwareConsoleSnapshot}
        onHardwareRefreshRequested={onHardwareRefreshRequested}
      />

      <section id="hardware-legacy" style={{ ...sectionStyle, display: 'none' }}>
        <h2>SovereignX Hardware Governor</h2>
        <p>The console now exposes a live hardware telemetry adapter and the governed promotion or retraction decision it produces.</p>
        <div style={gridStyle}>
          <Metric label="Source" value={telemetry.sovereignxHardware?.source ?? 'loading'} />
          <Metric label="Decision" value={telemetry.sovereignxHardware?.cycle.decision ?? 'loading'} />
          <Metric label="Headroom" value={telemetry.sovereignxHardware ? `${telemetry.sovereignxHardware.cycle.headroomC.toFixed(1)} °C` : 'loading'} />
          <Metric label="Load" value={telemetry.sovereignxHardware ? `${(telemetry.sovereignxHardware.cycle.loadFactor * 100).toFixed(1)}%` : 'loading'} />
        </div>
        <div style={gridStyle}>
          <Panel title="Telemetry">
            <p>CPU {telemetry.sovereignxHardware ? `${telemetry.sovereignxHardware.telemetry.cpuTempC.toFixed(1)} °C / ${telemetry.sovereignxHardware.telemetry.cpuVolt.toFixed(3)} V` : 'loading'}</p>
            <p>GPU {telemetry.sovereignxHardware ? `${telemetry.sovereignxHardware.telemetry.gpuTempC.toFixed(1)} °C / ${telemetry.sovereignxHardware.telemetry.gpuVolt.toFixed(3)} V` : 'loading'}</p>
            <p>Power {telemetry.sovereignxHardware ? `${(telemetry.sovereignxHardware.telemetry.powerDrawFraction * 100).toFixed(1)}%` : 'loading'}</p>
            <p>Utilization {telemetry.sovereignxHardware ? `${(telemetry.sovereignxHardware.telemetry.utilization * 100).toFixed(1)}%` : 'loading'}</p>
          </Panel>
          <Panel title="Thermal Bridge">
            <p>Vendor {telemetry.thermalBridge?.vendor ?? telemetry.sovereignxHardware?.thermalBridge?.vendor ?? 'loading'}</p>
            <p>Family {telemetry.thermalBridge?.deviceFamily ?? telemetry.sovereignxHardware?.thermalBridge?.deviceFamily ?? 'loading'}</p>
            <p>Hot sensor {telemetry.thermalBridge?.summary.hottestSensor ?? telemetry.sovereignxHardware?.thermalBridge?.summary.hottestSensor ?? 'loading'}</p>
            <p>Alerts {telemetry.thermalBridge?.summary.alertCount ?? telemetry.sovereignxHardware?.thermalBridge?.summary.alertCount ?? 0}</p>
          </Panel>
          <Panel title="Governor">
            <p>Frequency {telemetry.sovereignxHardware ? `${telemetry.sovereignxHardware.governor.state.currentFrequencyMhz.toFixed(1)} MHz` : 'loading'}</p>
            <p>Voltage {telemetry.sovereignxHardware ? `${telemetry.sovereignxHardware.governor.state.currentVoltageV.toFixed(3)} V` : 'loading'}</p>
            <p>Last decision {telemetry.sovereignxHardware?.governor.state.lastDecision ?? 'loading'}</p>
            <p>{telemetry.sovereignxHardware?.sourceDetail ?? 'No telemetry source selected yet'}</p>
          </Panel>
          <Panel title="Replay Store">
            <p>Available {telemetry.hardwareReplayStore?.available ? 'yes' : 'no'}</p>
            <p>Entries {telemetry.hardwareReplayStore?.entryCount ?? 0}</p>
            <p>Latest decision {telemetry.hardwareReplayStore?.latest?.decision ?? 'none'}</p>
            <p style={{ wordBreak: 'break-all' }}>{telemetry.hardwareReplayStore?.storePath ?? 'loading'}</p>
          </Panel>
          <Panel title="Override Drill">
            <p>Authority {telemetry.overrideDrill?.authority ?? 'loading'}</p>
            <p>Requested {telemetry.overrideDrill?.requestedDecision ?? 'loading'}</p>
            <p>Accepted {telemetry.overrideDrill?.accepted ? 'yes' : 'no'}</p>
            <p>Preview {telemetry.overrideDrill?.previewState.lastDecision ?? 'loading'}</p>
          </Panel>
          <Panel title="Replay Validation">
            <p>Baseline matches {telemetry.replayValidation?.baselineMatches ?? 0}</p>
            <p>Chaos quarantines {telemetry.replayValidation?.chaosQuarantines ?? 0}</p>
            <p>Passed {telemetry.replayValidation?.passed ? 'yes' : 'no'}</p>
            <p>{telemetry.replayValidation?.storePath ?? 'loading'}</p>
          </Panel>
          <Panel title="Hardware Benchmarks">
            {telemetry.hardwareBenchmarks ? (
              <>
                <div style={gridStyle}>
                  <Metric label="Latency gain" value={`${telemetry.hardwareBenchmarks.summary.estimatedLatencyReductionPct.toFixed(1)}%`} />
                  <Metric label="Throughput gain" value={`${telemetry.hardwareBenchmarks.summary.estimatedThroughputGainPct.toFixed(1)}%`} />
                  <Metric label="Efficiency gain" value={`${telemetry.hardwareBenchmarks.summary.estimatedCostEfficiencyGainPct.toFixed(1)}%`} />
                  <Metric label="Thermal delta" value={`${telemetry.hardwareBenchmarks.summary.thermalHeadroomDeltaC.toFixed(1)} °C`} />
                </div>
                <p style={subtleTextStyle}>{telemetry.hardwareBenchmarks.summary.recommendation}</p>
                <table>
                  <thead>
                    <tr>
                      <th>Metric</th>
                      <th>CPU baseline</th>
                      <th>Governed route</th>
                      <th>Delta</th>
                    </tr>
                  </thead>
                  <tbody>
                    {telemetry.hardwareBenchmarks.comparisons.map((comparison) => (
                      <tr key={comparison.metric}>
                        <td>{comparison.metric}</td>
                        <td>{formatBenchmarkNumber(comparison.baseline)}</td>
                        <td>{formatBenchmarkNumber(comparison.governed)}</td>
                        <td>{formatBenchmarkDelta(comparison.delta, comparison.metric)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div style={gridStyle}>
                  <Panel title="CPU baseline">
                    <p>Node {telemetry.hardwareBenchmarks.baselineScenario.nodeId ?? 'none'}</p>
                    <p>Backend {telemetry.hardwareBenchmarks.baselineScenario.backend}</p>
                    <p>Latency {formatBenchmarkNumber(telemetry.hardwareBenchmarks.baselineScenario.estimatedLatencyMs)} ms</p>
                    <p>Throughput {formatBenchmarkNumber(telemetry.hardwareBenchmarks.baselineScenario.estimatedThroughputOpsPerSec)} ops/s</p>
                    <p>Cost index {formatBenchmarkNumber(telemetry.hardwareBenchmarks.baselineScenario.estimatedCostIndex)}</p>
                  </Panel>
                  <Panel title="Governed route">
                    <p>Node {telemetry.hardwareBenchmarks.governedScenario.nodeId ?? 'none'}</p>
                    <p>Backend {telemetry.hardwareBenchmarks.governedScenario.backend}</p>
                    <p>Latency {formatBenchmarkNumber(telemetry.hardwareBenchmarks.governedScenario.estimatedLatencyMs)} ms</p>
                    <p>Throughput {formatBenchmarkNumber(telemetry.hardwareBenchmarks.governedScenario.estimatedThroughputOpsPerSec)} ops/s</p>
                    <p>Cost index {formatBenchmarkNumber(telemetry.hardwareBenchmarks.governedScenario.estimatedCostIndex)}</p>
                  </Panel>
                </div>
                <div style={gridStyle}>
                  {telemetry.hardwareBenchmarks.counterfactualScenarios.map((scenario) => (
                    <Panel key={scenario.scenarioId} title={scenario.label}>
                      <p>Node {scenario.nodeId ?? 'none'}</p>
                      <p>Backend {scenario.backend}</p>
                      <p>Latency {formatBenchmarkNumber(scenario.estimatedLatencyMs)} ms</p>
                      <p>Throughput {formatBenchmarkNumber(scenario.estimatedThroughputOpsPerSec)} ops/s</p>
                      <p>Throttle risk {formatBenchmarkNumber(scenario.estimatedThrottleRisk)}</p>
                    </Panel>
                  ))}
                </div>
                <p style={subtleTextStyle}>
                  Benchmark results are estimated from live telemetry and governed cluster routing. They are deterministic comparisons, not synthetic load tests.
                </p>
              </>
            ) : (
              <p style={subtleTextStyle}>Benchmark summary is loading.</p>
            )}
          </Panel>
          <Panel title="Cluster Routing">
            <p>Action {telemetry.sovereignxClusterRouting?.clusterDecision.action ?? 'loading'}</p>
            <p>Node {telemetry.sovereignxClusterRouting?.clusterDecision.nodeId ?? 'none'}</p>
            <p>Backend {telemetry.sovereignxClusterRouting?.clusterDecision.backend ?? 'loading'}</p>
            <p>Eligible {telemetry.sovereignxClusterRouting?.summary.eligibleNodeCount ?? 0} / {telemetry.sovereignxClusterRouting?.summary.nodeCount ?? 0}</p>
          </Panel>
        </div>
      </section>

      <section id="cluster" style={sectionStyle}>
        <h2>SovereignX Cluster Governance</h2>
        <p>The console now exposes live membership control, autoscaling and failover recommendations, soak and chaos validation, and the constitutional traceability matrix.</p>
        <div style={gridStyle}>
          <Metric label="Desired" value={String(telemetry.sovereignxClusterGovernance?.summary.desiredNodeCount ?? 0)} />
          <Metric label="Active" value={String(telemetry.sovereignxClusterGovernance?.summary.activeNodeCount ?? 0)} />
          <Metric label="Quarantined" value={String(telemetry.sovereignxClusterGovernance?.summary.quarantinedNodeCount ?? 0)} />
          <Metric label="Traceability" value={String(telemetry.constitutionalTraceability?.summary.capabilityCount ?? telemetry.sovereignxClusterGovernance?.traceabilityMatrix.summary.capabilityCount ?? 0)} />
        </div>
        <div style={gridStyle}>
          <Panel title="Membership Control">
            <p>Control state {telemetry.sovereignxClusterGovernance?.controlState.lastAction?.action ?? 'steady_state'}</p>
            <p>Preferred failover {telemetry.sovereignxClusterGovernance?.controlState.preferredFailoverNodeId ?? 'none'}</p>
            <p>Quarantined nodes {telemetry.sovereignxClusterGovernance?.controlState.quarantinedNodeIds.join(', ') || 'none'}</p>
            <p>Selection {telemetry.sovereignxClusterGovernance?.summary.selectionPolicy ?? 'loading'}</p>
          </Panel>
          <Panel title="Autoscaling and Failover">
            <p>Autoscaling {telemetry.sovereignxClusterGovernance?.autoscaling.action ?? 'loading'} {"->"} {telemetry.sovereignxClusterGovernance?.autoscaling.recommendedNodeCount ?? 0}</p>
            <p>Failover {telemetry.sovereignxClusterGovernance?.failover.action ?? 'loading'}</p>
            <p>Target {telemetry.sovereignxClusterGovernance?.failover.toNodeId ?? 'none'}</p>
            <p>Pressure {telemetry.sovereignxClusterGovernance ? telemetry.sovereignxClusterGovernance.autoscaling.pressureScore.toFixed(3) : 'loading'}</p>
          </Panel>
          <Panel title="Soak and Chaos">
            <p>Soak runs {telemetry.sovereignxClusterGovernance?.soakChaosValidation.soakRuns ?? 0}</p>
            <p>Stable selections {telemetry.sovereignxClusterGovernance?.soakChaosValidation.stableSelections ?? 0}</p>
            <p>Chaos runs {telemetry.sovereignxClusterGovernance?.soakChaosValidation.chaosRuns ?? 0}</p>
            <p>Passed {telemetry.sovereignxClusterGovernance?.soakChaosValidation.passed ? 'yes' : 'no'}</p>
          </Panel>
          <Panel title="Traceability Summary">
            <p>Capabilities {telemetry.constitutionalTraceability?.summary.capabilityCount ?? telemetry.sovereignxClusterGovernance?.traceabilityMatrix.summary.capabilityCount ?? 0}</p>
            <p>Requirements {telemetry.constitutionalTraceability?.summary.requirementCount ?? telemetry.sovereignxClusterGovernance?.traceabilityMatrix.summary.requirementCount ?? 0}</p>
            <p>Evidence {telemetry.constitutionalTraceability?.summary.evidenceCount ?? telemetry.sovereignxClusterGovernance?.traceabilityMatrix.summary.evidenceCount ?? 0}</p>
            <p>Tests {telemetry.constitutionalTraceability?.summary.testCount ?? telemetry.sovereignxClusterGovernance?.traceabilityMatrix.summary.testCount ?? 0}</p>
          </Panel>
        </div>
        <table>
          <thead>
            <tr>
              <th>Capability</th>
              <th>Requirements</th>
              <th>Component</th>
              <th>Evidence</th>
              <th>Tests</th>
            </tr>
          </thead>
          <tbody>
            {(telemetry.constitutionalTraceability?.rows ?? telemetry.sovereignxClusterGovernance?.traceabilityMatrix.rows ?? []).map((row) => (
              <tr key={row.capabilityId}>
                <td>{row.capabilityName}</td>
                <td>{row.constitutionalRequirements.join('; ')}</td>
                <td>{row.architecturalComponent}</td>
                <td>{row.evidenceIds.join(', ')}</td>
                <td>{row.tests.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section id="aais" style={sectionStyle}>
        <h2>AAIS Runtime</h2>
        <div style={gridStyle}>
          <Metric label="Link" value={telemetry.aais?.connected ? 'connected' : 'offline'} />
        <Metric label="Mode" value={telemetry.aais?.activeModelMode || 'unknown'} />
        <Metric label="AI" value={telemetry.aais?.aiStatus || telemetry.aais?.status || 'unknown'} />
        <Metric label="Legacy API" value={telemetry.aais?.legacyApiLoaded ? 'loaded' : 'pending'} />
      </div>
      <div style={gridStyle}>
        <Panel title="Bridge">
          <p>{telemetry.aais?.baseUrl ?? 'AAIS_BASE_URL unset'}</p>
          <p>{telemetry.aais?.mockModeActive ? 'mock mode active' : 'real/provider mode or offline'}</p>
          {telemetry.aais?.error ? <p>{telemetry.aais.error}</p> : null}
        </Panel>
        <Panel title="Contractors">
          <p>{String(telemetry.aais?.contractors?.length ?? 0)} contractor checks reported</p>
        </Panel>
      </div>
    </section>

      <section id="cab" style={sectionStyle}>
        <h2>CAB Continuity</h2>
      <div style={gridStyle}>
        <Metric label="Ledger" value={telemetry.cab?.available ? 'available' : 'empty'} />
        <Metric label="Entries" value={String(telemetry.cab?.entryCount ?? 0)} />
        <Metric label="Active" value={String(telemetry.cab?.activeCount ?? 0)} />
        <Metric label="Invariants" value={telemetry.cab?.invariants.passed ? 'pass' : 'review'} />
      </div>
      <div style={gridStyle}>
        <Panel title="Latest CAB Links">
          <p>Intent {telemetry.cab?.latest.intents[0] ?? 'none'}</p>
          <p>Decision {telemetry.cab?.latest.decisions[0] ?? 'none'}</p>
          <p>Evidence {telemetry.cab?.latest.evidenceChains[0] ?? 'none'}</p>
          <p>Receipt {telemetry.cab?.latest.continuityReceipts[0] ?? 'none'}</p>
        </Panel>
        <Panel title="Invariant Surface">
          <ul>
            {(telemetry.cab?.invariants.results ?? []).map((result) => (
              <li key={result.invariantId}>{result.invariantId}: {result.status}</li>
            ))}
          </ul>
        </Panel>
      </div>
      </section>

      <section id="cori-alpha" style={sectionStyle}>
        <h2>CORI Alpha Upload Intelligence</h2>
        <p>The operator console and customer workspace now read the same governed upload summary from the shared CORI Alpha ledger.</p>
        <CoriAlphaSummaryCard
          summary={coriAlpha}
          loading={false}
          title="CORI Alpha upload intelligence"
          surfaceLabel="Operator console view"
          emptyMessage="No CORI Alpha summary is available yet."
        />
      </section>
      <GovernanceEvolutionTimelinePanel
        governanceEvolution={governanceEvolution}
        selectedGovernanceEvolutionId={selectedGovernanceEvolutionId}
        onSelectedGovernanceEvolutionIdChange={onSelectedGovernanceEvolutionIdChange}
      />
    <PricingLedgerAndMarginDashboard pricing={telemetry.pricing} />
    <TreasurySchedulePanel treasurySchedule={treasurySchedule} />

    <section style={sectionStyle}>
      <h2>Customer Registry</h2>
      <p>Customer identities come from the platform API and carry plan assignment, routing tier, and entitlement flags.</p>
      <div style={gridStyle}>
        <Metric label="Customers" value={String(customers.customerCount)} />
        <Metric label="Free" value={String(customers.planCounts.free ?? 0)} />
        <Metric label="Pro" value={String(customers.planCounts.pro ?? 0)} />
        <Metric label="Enterprise" value={String(customers.planCounts.enterprise ?? 0)} />
      </div>
      <table>
        <thead>
          <tr>
            <th>Email</th>
            <th>Plan</th>
            <th>Routing</th>
            <th>Handoff</th>
            <th>Ledger</th>
            <th>Margin</th>
            <th>Audit</th>
          </tr>
        </thead>
        <tbody>
          {customers.customers.map((customer) => (
            <tr key={customer.id}>
              <td>{customer.email}</td>
              <td>{customer.planName}</td>
              <td>{customer.entitlements.routingTier}</td>
              <td>{customer.entitlements.codexPacketHandoff ? 'yes' : 'no'}</td>
              <td>{customer.entitlements.usageLedger ? 'yes' : 'no'}</td>
              <td>{customer.entitlements.marginDashboard ? 'yes' : 'no'}</td>
              <td>{customer.entitlements.auditScope}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
    <OrganizationRegistryRbacPanel organizations={organizations} />
    <OrganizationUsageAndAuditPanel
      organizationUsage={organizationUsage}
      organizationAudit={organizationAudit}
    />

    <CustomerQuotaEnforcementPanel quota={quota} />

    <CepArtifactDock
      cepArtifacts={cepArtifacts}
      selectedCepArtifactId={selectedCepArtifactId}
      onSelectedCepArtifactIdChange={onSelectedCepArtifactIdChange}
      cepTrustBandFilter={cepTrustBandFilter}
      cepTrustGovernanceFilter={cepTrustGovernanceFilter}
      cepTrustMinScoreFilter={cepTrustMinScoreFilter}
      onCepTrustBandFilterChange={onCepTrustBandFilterChange}
      onCepTrustGovernanceFilterChange={onCepTrustGovernanceFilterChange}
      onCepTrustMinScoreFilterChange={onCepTrustMinScoreFilterChange}
    />

    <ArenaModePanel arena={arenaMode} />

    <section style={sectionStyle}>
      <h2>Top Patterns</h2>
      <table>
        <thead><tr><th>Pattern</th><th>Fault codes</th><th>Recurrence</th><th>Last seen</th></tr></thead>
        <tbody>
          {telemetry.topPatterns.map((pattern) => (
            <tr key={pattern.patternId}>
              <td>{pattern.patternId}</td>
              <td>{pattern.faultCodes.join(', ')}</td>
              <td>{pattern.recurrence}</td>
              <td>{pattern.lastSeenAt}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>

    <PatchApprovals apiBase="" />
  </div>
  );
};

function isProofSurfaceSummary(value: unknown): value is ProofSurfaceSummary {
  return Boolean(
    value &&
      typeof value === 'object' &&
      'identity' in value &&
      'proofLevel' in value &&
      'commercialReadiness' in value &&
      'domain' in value &&
      'healthIndicator' in value,
  );
}

const sectionStyle: React.CSSProperties = {
  background: '#fff',
  border: '1px solid #dfe3e8',
  borderRadius: 8,
  padding: 16,
  marginBottom: 16,
};

const buttonStyle: React.CSSProperties = {
  border: '1px solid #23405f',
  borderRadius: 10,
  padding: '10px 14px',
  background: '#23405f',
  color: '#ffffff',
  fontWeight: 600,
  cursor: 'pointer',
};

const secondaryButtonStyle: React.CSSProperties = {
  ...buttonStyle,
  background: '#ffffff',
  color: '#23405f',
};

const subtleTextStyle: React.CSSProperties = {
  color: '#64748b',
  lineHeight: 1.6,
};

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
};

const groupSectionStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
};

const groupHeaderStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: 12,
};

const graphPillStyle: React.CSSProperties = {
  border: '1px solid #c8d4e3',
  borderRadius: 999,
  padding: '6px 12px',
  background: '#eef4ff',
  color: '#23405f',
  fontSize: 12,
  fontWeight: 700,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
};

const domainGridStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
};

const proofSurfaceCardStyle: React.CSSProperties = {
  appearance: 'none',
  border: '1px solid #d9e0ea',
  borderRadius: 14,
  padding: 14,
  background: '#ffffff',
  textAlign: 'left',
  cursor: 'pointer',
  display: 'grid',
  gap: 8,
};

const proofSurfaceCardHeaderStyle: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 8,
  justifyContent: 'space-between',
  alignItems: 'center',
};

const proofSurfaceBadgeStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  borderRadius: 999,
  padding: '4px 10px',
  fontSize: 11,
  fontWeight: 700,
  letterSpacing: '0.06em',
  textTransform: 'uppercase',
};

const domainBadgeStyles: Record<ProofSurfaceSummary['domain'], React.CSSProperties> = {
  Governance: { background: '#eef4ff', color: '#23405f' },
  Execution: { background: '#f2e8ff', color: '#5b21b6' },
  Runtime: { background: '#e8fff4', color: '#0f766e' },
  Intent: { background: '#fff4e8', color: '#9a3412' },
  Evidence: { background: '#f0f9ff', color: '#0369a1' },
  Verification: { background: '#ecfeff', color: '#155e75' },
  Replay: { background: '#f5f3ff', color: '#6d28d9' },
  Audit: { background: '#fdf2f8', color: '#be185d' },
  Interoperability: { background: '#f8fafc', color: '#475569' },
};

const healthBadgeStyles: Record<ProofSurfaceSummary['healthIndicator'], React.CSSProperties> = {
  Verified: { background: '#e7f7ef', color: '#146c43' },
  Experimental: { background: '#fff4d6', color: '#9a6700' },
  Simulated: { background: '#f1f5f9', color: '#475569' },
  Operational: { background: '#e0f2fe', color: '#075985' },
  'Commercially Available': { background: '#f3e8ff', color: '#6b21a8' },
};

const proofSurfaceCardTitleStyle: React.CSSProperties = {
  fontSize: 18,
  fontWeight: 800,
  color: '#172026',
};

const proofSurfaceCardIdentityStyle: React.CSSProperties = {
  fontSize: 12,
  color: '#5f6b7a',
  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
};

const proofSurfaceCardMetaStyle: React.CSSProperties = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: 10,
  fontSize: 12,
  color: '#334155',
  fontWeight: 600,
};

const proofSurfaceCardSummaryStyle: React.CSSProperties = {
  color: '#172026',
  lineHeight: 1.5,
};

const proofSurfaceCardFooterStyle: React.CSSProperties = {
  color: '#5f6b7a',
  fontSize: 13,
  lineHeight: 1.5,
};

const profilePanelStyle: React.CSSProperties = {
  border: '1px solid #c9d5e4',
  borderRadius: 16,
  padding: 16,
  background: '#f8fbff',
  display: 'grid',
  gap: 16,
};

const profileHeaderStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  gap: 16,
  alignItems: 'start',
};

const profileEyebrowStyle: React.CSSProperties = {
  color: '#23405f',
  textTransform: 'uppercase',
  letterSpacing: '0.12em',
  fontSize: 11,
  fontWeight: 800,
};

const profileIdentityStyle: React.CSSProperties = {
  color: '#5f6b7a',
  fontSize: 12,
  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
};

const profileLeadStyle: React.CSSProperties = {
  margin: 0,
  color: '#334155',
  lineHeight: 1.6,
};

const profileTwoColumnStyle: React.CSSProperties = {
  display: 'grid',
  gap: 12,
  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
};

const relatedSurfaceLinkStyle: React.CSSProperties = {
  border: 0,
  background: 'transparent',
  color: '#1d4ed8',
  padding: 0,
  cursor: 'pointer',
  font: 'inherit',
  textAlign: 'left',
};

const Panel: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={{ border: '1px solid #e3e7ed', borderRadius: 6, padding: 12 }}>
    <h3 style={{ marginTop: 0 }}>{title}</h3>
    {children}
  </div>
);

const Metric: React.FC<{ label: string; value: string }> = ({ label, value }) => (
  <div style={{ border: '1px solid #e3e7ed', borderRadius: 6, padding: 12 }}>
    <div style={{ color: '#5f6b7a', fontSize: 12, textTransform: 'uppercase' }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 700 }}>{value}</div>
  </div>
);

const BenchmarkCard: React.FC<{
  label: string;
  score: number;
  delta: number;
  markers: { current: number; previous: number; industry: number; topQuartile: number };
}> = ({ label, score, delta, markers }) => (
  <div style={{ border: '1px solid #e3e7ed', borderRadius: 6, padding: 12 }}>
    <div style={{ color: '#5f6b7a', fontSize: 12, textTransform: 'uppercase' }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 700 }}>{score}</div>
    <div style={{ height: 8, background: '#e8edf2', borderRadius: 4, position: 'relative', margin: '8px 0' }}>
      <span style={markerStyle(markers.industry, '#677483')} />
      <span style={markerStyle(markers.previous, '#9aa5b1')} />
      <span style={markerStyle(markers.topQuartile, '#2f6fed')} />
      <span style={markerStyle(markers.current, '#138a5e', 8)} />
    </div>
    <div>Delta {formatDelta(delta)}</div>
  </div>
);

const PROOF_SURFACE_DOMAIN_ORDER: ProofSurfaceSummary['domain'][] = [
  'Governance',
  'Execution',
  'Runtime',
  'Intent',
  'Evidence',
  'Verification',
  'Replay',
  'Audit',
  'Interoperability',
];

const ProofSurfaceKnowledgeGraph: React.FC<{
  surfaces: ProofSurfaceSummary[];
  selectedProofSurfaceId: string | null;
  onSelectedProofSurfaceChange: (value: string) => void;
}> = ({ surfaces, selectedProofSurfaceId, onSelectedProofSurfaceChange }) => {
  const groupedSurfaces = groupProofSurfacesByDomain(surfaces);
  const selectedSurface = findProofSurfaceById(surfaces, selectedProofSurfaceId) ?? surfaces[0];
  const verifiedCount = surfaces.filter((surface) => surface.healthIndicator === 'Verified').length;
  const operationalCount = surfaces.filter((surface) => surface.healthIndicator === 'Operational').length;
  const simulatedCount = surfaces.filter((surface) => surface.healthIndicator === 'Simulated').length;
  const commercialCount = surfaces.filter((surface) => surface.healthIndicator === 'Commercially Available').length;

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div style={gridStyle}>
        <Metric label="Surfaces" value={String(surfaces.length)} />
        <Metric label="Domains" value={String(groupedSurfaces.length)} />
        <Metric label="Verified" value={String(verifiedCount)} />
        <Metric label="Operational" value={String(operationalCount)} />
        <Metric label="Simulated" value={String(simulatedCount)} />
        <Metric label="Commercial" value={String(commercialCount)} />
      </div>

      {groupedSurfaces.map((group) => (
        <section key={group.domain} style={groupSectionStyle}>
          <div style={groupHeaderStyle}>
            <div>
              <h3 style={{ margin: 0 }}>{group.domain}</h3>
              <p style={{ margin: '4px 0 0', color: '#5f6b7a', fontSize: 13 }}>
                {group.surfaces.length} surface{group.surfaces.length === 1 ? '' : 's'}
              </p>
            </div>
            <div style={graphPillStyle}>Constitutional knowledge graph</div>
          </div>
          <div style={domainGridStyle}>
            {group.surfaces.map((surface) => (
              <ProofSurfaceCard
                key={surface.identity.id}
                surface={surface}
                selected={surface.identity.id === selectedSurface?.identity.id}
                onSelect={onSelectedProofSurfaceChange}
              />
            ))}
          </div>
        </section>
      ))}

      {selectedSurface ? (
        <ProofSurfaceProfilePanel
          surface={selectedSurface}
          surfaces={surfaces}
          onSelectSurface={onSelectedProofSurfaceChange}
        />
      ) : null}

      <RouterProofSurfaceCallout surfaces={surfaces} />
    </div>
  );
};

const ProofSurfaceCard: React.FC<{
  surface: ProofSurfaceSummary;
  selected: boolean;
  onSelect: (value: string) => void;
}> = ({ surface, selected, onSelect }) => (
  <button
    type="button"
    onClick={() => onSelect(surface.identity.id)}
    style={{
      ...proofSurfaceCardStyle,
      borderColor: selected ? '#1d4ed8' : '#d9e0ea',
      boxShadow: selected ? '0 0 0 2px rgba(29, 78, 216, 0.12)' : 'none',
    }}
  >
    <div style={proofSurfaceCardHeaderStyle}>
      <span style={{ ...proofSurfaceBadgeStyle, ...domainBadgeStyles[surface.domain] }}>{surface.domain}</span>
      <span style={{ ...proofSurfaceBadgeStyle, ...healthBadgeStyles[surface.healthIndicator] }}>{surface.healthIndicator}</span>
    </div>
    <div style={proofSurfaceCardTitleStyle}>{surface.identity.name}</div>
    <div style={proofSurfaceCardIdentityStyle}>{surface.identity.id}</div>
    <div style={proofSurfaceCardMetaStyle}>
      <span>Proof {surface.proofLevel}</span>
      <span>Maturity {surface.maturity}</span>
      <span>Replay {surface.replayStatus}</span>
    </div>
    <div style={proofSurfaceCardSummaryStyle}>{surface.whatItProves}</div>
    <div style={proofSurfaceCardFooterStyle}>{surface.truthBoundary}</div>
  </button>
);

const ProofSurfaceProfilePanel: React.FC<{
  surface: ProofSurfaceSummary;
  surfaces: ProofSurfaceSummary[];
  onSelectSurface: (value: string) => void;
}> = ({ surface, surfaces, onSelectSurface }) => {
  const relatedSurfaces = surface.relatedProofSurfaces
    .map((relatedId) => findProofSurfaceById(surfaces, relatedId))
    .filter((relatedSurface): relatedSurface is ProofSurfaceSummary => Boolean(relatedSurface));

  return (
    <div style={profilePanelStyle}>
      <div style={profileHeaderStyle}>
        <div>
          <div style={profileEyebrowStyle}>{surface.domain}</div>
          <h3 style={{ margin: '4px 0 0' }}>{surface.identity.name}</h3>
          <div style={profileIdentityStyle}>{surface.identity.id}</div>
        </div>
        <div style={{ ...proofSurfaceBadgeStyle, ...healthBadgeStyles[surface.healthIndicator] }}>{surface.healthIndicator}</div>
      </div>

      <p style={profileLeadStyle}>{surface.whatItProves}</p>

      <div style={gridStyle}>
        <Metric label="Proof level" value={surface.proofLevel} />
        <Metric label="Maturity" value={surface.maturity} />
        <Metric label="Verification" value={surface.verificationStatus} />
        <Metric label="Replay" value={surface.replayStatus} />
      </div>

      <div style={profileTwoColumnStyle}>
        <Panel title="What it proves">
          <p>{surface.whatItProves}</p>
        </Panel>
        <Panel title="What it does not prove">
          <p>{surface.whatItDoesNotProve}</p>
        </Panel>
        <Panel title="Current evidence">
          <ul>
            {surface.currentEvidence.map((evidence) => (
              <li key={evidence.id}>
                <strong>{evidence.id}</strong>: {evidence.statement}
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="Blindspots">
          <ul>{surface.blindspots.map((item) => <li key={item}>{item}</li>)}</ul>
        </Panel>
        <Panel title="Known limitations">
          <ul>{surface.knownLimitations.map((item) => <li key={item}>{item}</li>)}</ul>
        </Panel>
        <Panel title="Adversarial claims">
          <ul>{surface.adversarialClaims.map((item) => <li key={item}>{item}</li>)}</ul>
        </Panel>
        <Panel title="Battle scars">
          <ul>{surface.battleScars.map((item) => <li key={item}>{item}</li>)}</ul>
        </Panel>
        <Panel title="Dependencies">
          <ul>{surface.dependencies.map((item) => <li key={item}>{item}</li>)}</ul>
        </Panel>
        <Panel title="Related proof surfaces">
          {relatedSurfaces.length > 0 ? (
            <ul>
              {relatedSurfaces.map((relatedSurface) => (
                <li key={relatedSurface.identity.id}>
                  <button
                    type="button"
                    onClick={() => onSelectSurface(relatedSurface.identity.id)}
                    style={relatedSurfaceLinkStyle}
                  >
                    {relatedSurface.identity.name} ({relatedSurface.domain})
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p>No related proof surfaces are currently linked in the graph.</p>
          )}
        </Panel>
        <Panel title="Graph metadata">
          <p><strong>Inputs:</strong> {surface.inputs.join(', ')}</p>
          <p><strong>Outputs:</strong> {surface.outputs.join(', ')}</p>
          <p><strong>Evidence receipts:</strong> {surface.evidenceReceipts.join(', ')}</p>
          <p><strong>Replay path:</strong> {surface.replayPath}</p>
          <p><strong>Verification path:</strong> {surface.verificationPath}</p>
          <p><strong>Truth boundary:</strong> {surface.truthBoundary}</p>
          <p><strong>Constitutional limits:</strong> {surface.constitutionalLimits}</p>
        </Panel>
      </div>
    </div>
  );
};

const TraceabilityMatrixCallout: React.FC<{ surfaces: ProofSurfaceSummary[] }> = ({ surfaces }) => {
  const traceabilitySurface = findProofSurfaceById(surfaces, '@cis-core/standards-traceability-matrix');
  if (!traceabilitySurface) {
    return null;
  }

  return (
    <div style={{ marginBottom: 16, border: '1px solid #cad4e0', borderRadius: 8, padding: 16, background: '#fffdf6' }}>
      <h3 style={{ marginTop: 0 }}>Traceability Matrix</h3>
      <p style={{ marginTop: 0 }}>
        The constitutional traceability matrix is published as a first-class proof surface and drives the generated conformance suite input.
      </p>
      <div style={gridStyle}>
        <Metric label="Proof Level" value={traceabilitySurface.proofLevel} />
        <Metric label="Verification" value={traceabilitySurface.verificationStatus} />
        <Metric label="Replay" value={traceabilitySurface.replayStatus} />
        <Metric label="Operational" value={traceabilitySurface.operationalStatus} />
      </div>
      <p style={{ marginBottom: 0, color: '#5f6b7a' }}>{traceabilitySurface.truthBoundary}</p>
    </div>
  );
};

const RouterProofSurfaceCallout: React.FC<{ surfaces: ProofSurfaceSummary[] }> = ({ surfaces }) => {
  const routerSurface = findRouterSurface(surfaces);
  if (!routerSurface) {
    return null;
  }

  return (
    <div style={{ marginTop: 16, border: '1px solid #cad4e0', borderRadius: 8, padding: 16, background: '#f8fbff' }}>
      <h3 style={{ marginTop: 0 }}>SovereignX Router</h3>
      <p style={{ marginTop: 0 }}>
        CPU governance handles planning, continuity, throttling, and invariants while GPU acceleration handles matmul,
        attention, render passes, and physics.
      </p>
      <div style={gridStyle}>
        <Metric label="Proof Level" value={routerSurface.proofLevel} />
        <Metric label="Verification" value={routerSurface.verificationStatus} />
        <Metric label="Replay" value={routerSurface.replayStatus} />
        <Metric label="Operational" value={routerSurface.operationalStatus} />
      </div>
      <p style={{ marginBottom: 0, color: '#5f6b7a' }}>{routerSurface.truthBoundary}</p>
      <p style={{ marginBottom: 0 }}>
        Failure path: delay, throttle, quarantine, or drop governed work when invariants or CIEMS limits require it.
      </p>
    </div>
  );
};

function groupProofSurfacesByDomain(surfaces: ProofSurfaceSummary[]): { domain: ProofSurfaceSummary['domain']; surfaces: ProofSurfaceSummary[] }[] {
  const grouped = new Map<ProofSurfaceSummary['domain'], ProofSurfaceSummary[]>();
  for (const surface of surfaces) {
    const bucket = grouped.get(surface.domain) ?? [];
    bucket.push(surface);
    grouped.set(surface.domain, bucket);
  }

  return [
    ...PROOF_SURFACE_DOMAIN_ORDER.filter((domain) => grouped.has(domain)).map((domain) => ({
      domain,
      surfaces: grouped.get(domain) ?? [],
    })),
    ...[...grouped.keys()]
      .filter((domain) => !PROOF_SURFACE_DOMAIN_ORDER.includes(domain))
      .sort()
      .map((domain) => ({
        domain,
        surfaces: grouped.get(domain) ?? [],
      })),
  ];
}

function findProofSurfaceById(
  surfaces: ProofSurfaceSummary[],
  identity: string | null,
): ProofSurfaceSummary | undefined {
  if (!identity) {
    return undefined;
  }
  return surfaces.find((surface) => surface.identity.id === identity);
}

function findRouterSurface(surfaces: ProofSurfaceSummary[]): ProofSurfaceSummary | undefined {
  return surfaces.find((surface) =>
    surface.identity.id === '@aaes-os/sovereignx-router' ||
    surface.identity.name.toLowerCase().includes('sovereignx router') ||
    surface.identity.name.toLowerCase().includes('sovereignxrouter'),
  );
}

function markerStyle(value: number, color: string, size = 6): React.CSSProperties {
  return {
    position: 'absolute',
    left: `${Math.max(0, Math.min(100, value))}%`,
    top: '50%',
    width: size,
    height: size,
    background: color,
    borderRadius: '50%',
    transform: 'translate(-50%, -50%)',
  };
}

function formatDelta(value: number): string {
  return value >= 0 ? `+${value}` : String(value);
}

function formatBenchmarkNumber(value: number): string {
  if (!Number.isFinite(value)) {
    return 'n/a';
  }

  const absolute = Math.abs(value);
  return absolute >= 100 ? value.toFixed(0) : value.toFixed(2);
}

function formatBenchmarkDelta(value: number, metric: string): string {
  const formatted = value >= 0 ? `+${formatBenchmarkNumber(value)}` : formatBenchmarkNumber(value);
  if (metric.toLowerCase().includes('latency') || metric.toLowerCase().includes('cost') || metric.toLowerCase().includes('throttle')) {
    return `${formatted} (${value >= 0 ? 'worse' : 'better'})`;
  }
  return `${formatted} (${value >= 0 ? 'better' : 'worse'})`;
}






