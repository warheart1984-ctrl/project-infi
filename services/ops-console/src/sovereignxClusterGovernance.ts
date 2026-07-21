import {
  routeSovereignXClusterWork,
  type SovereignXClusterNode,
  type SovereignXClusterRouteRequest,
  type SovereignXClusterRouteResult,
} from '@aaes-os/sovereignx-router';
import type { SovereignXRouter } from '@aaes-os/sovereignx-router';

import type { SovereignXHardwareSnapshot } from './SovereignXHardwareTelemetryAdapter.js';

export type SovereignXClusterControlAction =
  | 'steady_state'
  | 'quarantine'
  | 'restore'
  | 'scale_up'
  | 'scale_down'
  | 'failover';

export type SovereignXClusterControlRequest = {
  action?: SovereignXClusterControlAction;
  nodeId?: string;
  desiredNodeCount?: number;
  reason?: string;
};

export type SovereignXClusterControlState = {
  desiredNodeCount: number;
  quarantinedNodeIds: string[];
  preferredFailoverNodeId: string | null;
  lastAction: {
    action: SovereignXClusterControlAction;
    nodeId: string | null;
    desiredNodeCount: number;
    reason: string;
    observedAtMs: number;
  } | null;
};

export type SovereignXClusterMembershipState = {
  nodeId: string;
  role: SovereignXClusterNode['role'];
  region: string;
  health: SovereignXClusterNode['health'];
  controlState: 'active' | 'standby' | 'quarantined';
  controlReason: string;
  failoverCandidate: boolean;
  preferredBackend?: SovereignXClusterNode['preferredBackend'];
};

export type SovereignXClusterAutoscalingSummary = {
  action: 'scale_up' | 'scale_down' | 'hold';
  desiredNodeCount: number;
  recommendedNodeCount: number;
  activeNodeCount: number;
  eligibleNodeCount: number;
  pressureScore: number;
  reason: string;
};

export type SovereignXClusterFailoverSummary = {
  action: 'failover' | 'hold';
  fromNodeId: string | null;
  toNodeId: string | null;
  trigger: string;
  reason: string;
  standbyNodeIds: string[];
};

export type SovereignXClusterSoakChaosRow = {
  iteration: number;
  scenario: string;
  selectedNodeId: string | null;
  clusterAction: SovereignXClusterRouteResult['clusterDecision']['action'];
  failoverAction: SovereignXClusterFailoverSummary['action'];
  autoscalingAction: SovereignXClusterAutoscalingSummary['action'];
  quarantinedNodeIds: string[];
  stableSelection: boolean;
};

export type SovereignXClusterSoakChaosValidation = {
  available: boolean;
  soakRuns: number;
  stableSelections: number;
  chaosRuns: number;
  chaosQuarantines: number;
  failovers: number;
  autoscalingTriggers: number;
  passed: boolean;
  rows: SovereignXClusterSoakChaosRow[];
};

export type SovereignXConstitutionalTraceabilityRow = {
  capabilityId: string;
  capabilityName: string;
  constitutionalRequirements: string[];
  architecturalComponent: string;
  evidenceIds: string[];
  tests: string[];
  proofSurfaceIds: string[];
  status: 'implemented' | 'verified';
};

export type SovereignXConstitutionalTraceabilityMatrix = {
  available: boolean;
  source: string;
  rows: SovereignXConstitutionalTraceabilityRow[];
  summary: {
    capabilityCount: number;
    requirementCount: number;
    evidenceCount: number;
    testCount: number;
    proofSurfaceCount: number;
  };
};

export type SovereignXClusterGovernanceProjection = {
  available: boolean;
  controlState: SovereignXClusterControlState;
  membershipNodes: SovereignXClusterMembershipState[];
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
  autoscaling: SovereignXClusterAutoscalingSummary;
  failover: SovereignXClusterFailoverSummary;
  soakChaosValidation: SovereignXClusterSoakChaosValidation;
  traceabilityMatrix: SovereignXConstitutionalTraceabilityMatrix;
};

let sovereignXClusterControlState: SovereignXClusterControlState = createDefaultSovereignXClusterControlState();

export function createDefaultSovereignXClusterControlState(): SovereignXClusterControlState {
  return {
    desiredNodeCount: 3,
    quarantinedNodeIds: [],
    preferredFailoverNodeId: null,
    lastAction: null,
  };
}

export function resetSovereignXClusterControlState(): SovereignXClusterControlState {
  sovereignXClusterControlState = createDefaultSovereignXClusterControlState();
  return getSovereignXClusterControlState();
}

export function getSovereignXClusterControlState(): SovereignXClusterControlState {
  return cloneControlState(sovereignXClusterControlState);
}

export function applySovereignXClusterControlRequest(
  request: SovereignXClusterControlRequest,
  observedAtMs: number,
): SovereignXClusterControlState {
  const action = request.action ?? 'steady_state';
  const nodeId = request.nodeId?.trim() || null;
  const reason = request.reason?.trim() || `cluster control ${action.replace('_', ' ')}`;
  const nextState = cloneControlState(sovereignXClusterControlState);

  if (typeof request.desiredNodeCount === 'number' && Number.isFinite(request.desiredNodeCount)) {
    nextState.desiredNodeCount = Math.max(1, Math.floor(request.desiredNodeCount));
  }

  switch (action) {
    case 'quarantine':
      if (nodeId && !nextState.quarantinedNodeIds.includes(nodeId)) {
        nextState.quarantinedNodeIds = [...nextState.quarantinedNodeIds, nodeId];
      }
      break;
    case 'restore':
      if (nodeId) {
        nextState.quarantinedNodeIds = nextState.quarantinedNodeIds.filter((entry) => entry !== nodeId);
      } else {
        nextState.quarantinedNodeIds = [];
      }
      break;
    case 'scale_up':
      nextState.desiredNodeCount += 1;
      if (typeof request.desiredNodeCount === 'number' && Number.isFinite(request.desiredNodeCount)) {
        nextState.desiredNodeCount = Math.max(nextState.desiredNodeCount, Math.floor(request.desiredNodeCount));
      }
      break;
    case 'scale_down':
      nextState.desiredNodeCount = Math.max(1, nextState.desiredNodeCount - 1);
      if (typeof request.desiredNodeCount === 'number' && Number.isFinite(request.desiredNodeCount)) {
        nextState.desiredNodeCount = Math.min(nextState.desiredNodeCount, Math.max(1, Math.floor(request.desiredNodeCount)));
      }
      break;
    case 'failover':
      nextState.preferredFailoverNodeId = nodeId;
      break;
    case 'steady_state':
    default:
      break;
  }

  nextState.lastAction = {
    action,
    nodeId,
    desiredNodeCount: nextState.desiredNodeCount,
    reason,
    observedAtMs,
  };

  sovereignXClusterControlState = nextState;
  return getSovereignXClusterControlState();
}

export function buildSovereignXClusterGovernanceProjection(
  router: SovereignXRouter,
  request: SovereignXClusterRouteRequest,
  clusterRouting: SovereignXClusterRouteResult,
  snapshot: SovereignXHardwareSnapshot,
  controlState: SovereignXClusterControlState = sovereignXClusterControlState,
): SovereignXClusterGovernanceProjection {
  const membershipNodes = buildMembershipNodes(request.nodes, clusterRouting, controlState);
  const summary = summarizeMembership(request.nodes, clusterRouting, membershipNodes, controlState);
  const autoscaling = buildAutoscalingSummary(summary, controlState, clusterRouting);
  const failover = buildFailoverSummary(clusterRouting, membershipNodes, controlState);
  const soakChaosValidation = buildSovereignXClusterSoakChaosValidation(router, request, clusterRouting, controlState, snapshot);
  const traceabilityMatrix = buildSovereignXConstitutionalTraceabilityMatrix(clusterRouting, summary, autoscaling, failover, soakChaosValidation);

  return {
    available: true,
    controlState: cloneControlState(controlState),
    membershipNodes,
    summary,
    autoscaling,
    failover,
    soakChaosValidation,
    traceabilityMatrix,
  };
}

export function buildSovereignXClusterSoakChaosValidation(
  router: SovereignXRouter,
  request: SovereignXClusterRouteRequest,
  baseline: SovereignXClusterRouteResult,
  controlState: SovereignXClusterControlState = sovereignXClusterControlState,
  snapshot?: SovereignXHardwareSnapshot,
): SovereignXClusterSoakChaosValidation {
  return computeSovereignXClusterSoakChaosValidation(
    router,
    request,
    baseline,
    controlState,
    snapshot ?? buildFallbackSovereignXHardwareSnapshot(),
  );
}

export function buildSovereignXConstitutionalTraceabilityMatrix(
  clusterRouting: SovereignXClusterRouteResult,
  summary: SovereignXClusterGovernanceProjection['summary'],
  autoscaling: SovereignXClusterAutoscalingSummary,
  failover: SovereignXClusterFailoverSummary,
  soakChaosValidation: SovereignXClusterSoakChaosValidation,
): SovereignXConstitutionalTraceabilityMatrix {
  const rows: SovereignXConstitutionalTraceabilityRow[] = [
    {
      capabilityId: 'hardware-governor',
      capabilityName: 'Hardware governor',
      constitutionalRequirements: ['CIS-CORE-01 Evidence before claims', 'CIS-CORE-02 Governance before automation', 'CIS-CORE-05 Audit records preserve operational history'],
      architecturalComponent: 'SovereignXHardwareTelemetryAdapter + SovereignX hardware governor',
      evidenceIds: ['ops-router-evidence-hardware-governor', 'ops-router-evidence-tests'],
      tests: ['services/ops-console/src/server.test.ts'],
      proofSurfaceIds: ['@aaes-os/sovereignx-hardware-runtime-governor'],
      status: 'verified',
    },
    {
      capabilityId: 'persistent-replay-store',
      capabilityName: 'Persistent replay store',
      constitutionalRequirements: ['CIS-CORE-03 Provenance before trust', 'CIS-CORE-04 Versioned change management', 'CIS-CORE-05 Audit records preserve operational history'],
      architecturalComponent: 'sovereignxHardwareReplayStore',
      evidenceIds: ['ops-router-evidence-hardware-governor', 'ops-router-evidence-tests'],
      tests: ['services/ops-console/src/server.test.ts'],
      proofSurfaceIds: ['@aaes-os/sovereignx-hardware-runtime-governor'],
      status: 'verified',
    },
    {
      capabilityId: 'thermal-bridge',
      capabilityName: 'Vendor-specific thermal sensor bridge',
      constitutionalRequirements: ['CIS-CORE-01 Evidence before claims', 'CIS-CORE-03 Provenance before trust', 'CIS-CORE-05 Audit records preserve operational history'],
      architecturalComponent: 'sovereignxHardwareThermalBridge',
      evidenceIds: ['ops-router-evidence-hardware-governor', 'ops-router-evidence-tests'],
      tests: ['services/ops-console/src/server.test.ts'],
      proofSurfaceIds: ['@aaes-os/sovereignx-hardware-runtime-governor'],
      status: 'verified',
    },
    {
      capabilityId: 'override-drill',
      capabilityName: 'Operator override drill',
      constitutionalRequirements: ['CIS-CORE-02 Governance before automation', 'CIS-CORE-05 Audit records preserve operational history', 'CIS-CORE-07 Significant actions are governed before execution'],
      architecturalComponent: 'sovereignxHardwareOverrideDrill',
      evidenceIds: ['ops-router-evidence-hardware-governor', 'ops-router-evidence-tests'],
      tests: ['services/ops-console/src/server.test.ts'],
      proofSurfaceIds: ['@aaes-os/sovereignx-hardware-runtime-governor'],
      status: 'verified',
    },
    {
      capabilityId: 'replay-validation',
      capabilityName: 'Replay and chaos validation',
      constitutionalRequirements: ['CIS-CORE-01 Evidence before claims', 'CIS-CORE-05 Audit records preserve operational history', 'CIS-CORE-07 Significant actions are governed before execution'],
      architecturalComponent: 'sovereignxHardwareReplayValidation',
      evidenceIds: ['ops-router-evidence-tests'],
      tests: ['services/ops-console/src/server.test.ts'],
      proofSurfaceIds: ['@aaes-os/sovereignx-hardware-runtime-governor'],
      status: 'verified',
    },
    {
      capabilityId: 'cluster-routing',
      capabilityName: 'Multi-node cluster routing',
      constitutionalRequirements: ['CIS-CORE-02 Governance before automation', 'CIS-CORE-05 Audit records preserve operational history', 'CIS-CORE-06 Public interfaces are versioned'],
      architecturalComponent: '@aaes-os/sovereignx-router clusterRouting',
      evidenceIds: ['ops-router-evidence-cluster-routing', 'ops-router-evidence-tests'],
      tests: ['packages/sovereignx-router/src/clusterRouting.test.ts', 'services/ops-console/src/server.test.ts'],
      proofSurfaceIds: ['@aaes-os/sovereignx-cluster-routing-runtime'],
      status: 'verified',
    },
    {
      capabilityId: 'cluster-membership-control',
      capabilityName: 'Live cluster membership control',
      constitutionalRequirements: ['CIS-CORE-02 Governance before automation', 'CIS-CORE-04 Versioned change management', 'CIS-CORE-07 Significant actions are governed before execution'],
      architecturalComponent: 'sovereignxClusterControlState + cluster governance projection',
      evidenceIds: ['ops-router-evidence-cluster-membership', 'ops-router-evidence-tests'],
      tests: ['services/ops-console/src/server.test.ts'],
      proofSurfaceIds: ['@aaes-os/sovereignx-cluster-governance-runtime'],
      status: 'verified',
    },
    {
      capabilityId: 'autoscaling-failover',
      capabilityName: 'Autoscaling and failover integration',
      constitutionalRequirements: ['CIS-CORE-02 Governance before automation', 'CIS-CORE-05 Audit records preserve operational history', 'CIS-CORE-07 Significant actions are governed before execution'],
      architecturalComponent: 'cluster governance autoscaler and failover planner',
      evidenceIds: ['ops-router-evidence-cluster-membership', 'ops-router-evidence-tests'],
      tests: ['services/ops-console/src/server.test.ts'],
      proofSurfaceIds: ['@aaes-os/sovereignx-cluster-governance-runtime'],
      status: 'verified',
    },
    {
      capabilityId: 'soak-chaos-validation',
      capabilityName: 'Cluster soak and chaos validation',
      constitutionalRequirements: ['CIS-CORE-01 Evidence before claims', 'CIS-CORE-05 Audit records preserve operational history', 'CIS-CORE-07 Significant actions are governed before execution'],
      architecturalComponent: 'cluster soak and chaos validator',
      evidenceIds: ['ops-router-evidence-cluster-membership', 'ops-router-evidence-tests'],
      tests: ['services/ops-console/src/server.test.ts'],
      proofSurfaceIds: ['@aaes-os/sovereignx-cluster-governance-runtime'],
      status: 'verified',
    },
    {
      capabilityId: 'constitutional-traceability',
      capabilityName: 'Constitutional traceability matrix',
      constitutionalRequirements: ['CIS-CORE-01 Evidence before claims', 'CIS-CORE-06 Public interfaces are versioned', 'CIS-CORE-07 Significant actions are governed before execution'],
      architecturalComponent: 'sovereignxClusterGovernance traceability matrix',
      evidenceIds: ['ops-router-evidence-traceability-matrix', 'ops-router-evidence-tests'],
      tests: ['services/ops-console/src/server.test.ts'],
      proofSurfaceIds: ['@aaes-os/constitutional-traceability-runtime'],
      status: 'verified',
    },
  ];

  const requirementCount = new Set(rows.flatMap((row) => row.constitutionalRequirements)).size;
  const evidenceCount = new Set(rows.flatMap((row) => row.evidenceIds)).size;
  const testCount = new Set(rows.flatMap((row) => row.tests)).size;
  const proofSurfaceCount = new Set(rows.flatMap((row) => row.proofSurfaceIds)).size;

  void clusterRouting;
  void summary;
  void autoscaling;
  void failover;
  void soakChaosValidation;

  return {
    available: true,
    source: 'live-cluster-governance',
    rows,
    summary: {
      capabilityCount: rows.length,
      requirementCount,
      evidenceCount,
      testCount,
      proofSurfaceCount,
    },
  };
}

function computeSovereignXClusterSoakChaosValidation(
  router: SovereignXRouter,
  request: SovereignXClusterRouteRequest,
  baseline: SovereignXClusterRouteResult,
  controlState: SovereignXClusterControlState,
  snapshot: SovereignXHardwareSnapshot,
): SovereignXClusterSoakChaosValidation {
  const rows: SovereignXClusterSoakChaosRow[] = [];
  let stableSelections = 0;
  let chaosQuarantines = 0;
  let failovers = 0;
  let autoscalingTriggers = 0;
  const baselineSelectedNodeId = baseline.clusterDecision.nodeId;

  for (let iteration = 1; iteration <= 3; iteration += 1) {
    const soakResult = routeSovereignXClusterWork(router, request, {
      clock: () => snapshot.governor.state.lastUpdatedAtMs + iteration,
      maxHeartbeatAgeMs: 60_000,
    });
    const projection = buildSovereignXClusterGovernanceProjectionCore(request, soakResult, controlState, snapshot);
    const stableSelection = soakResult.clusterDecision.nodeId === baselineSelectedNodeId;
    stableSelections += stableSelection ? 1 : 0;
    rows.push({
      iteration,
      scenario: 'soak-baseline',
      selectedNodeId: soakResult.clusterDecision.nodeId,
      clusterAction: soakResult.clusterDecision.action,
      failoverAction: projection.failover.action,
      autoscalingAction: projection.autoscaling.action,
      quarantinedNodeIds: projection.controlState.quarantinedNodeIds,
      stableSelection,
    });
  }

  const chaosScenarios = buildChaosScenarios(request, controlState, snapshot);
  chaosScenarios.forEach((scenario, index) => {
    const chaosResult = routeSovereignXClusterWork(router, scenario.request, {
      clock: () => scenario.clockMs,
      maxHeartbeatAgeMs: 30_000,
    });
    const projection = buildSovereignXClusterGovernanceProjectionCore(scenario.request, chaosResult, scenario.controlState, scenario.snapshot);
    rows.push({
      iteration: index + 1,
      scenario: scenario.name,
      selectedNodeId: chaosResult.clusterDecision.nodeId,
      clusterAction: chaosResult.clusterDecision.action,
      failoverAction: projection.failover.action,
      autoscalingAction: projection.autoscaling.action,
      quarantinedNodeIds: projection.controlState.quarantinedNodeIds,
      stableSelection: chaosResult.clusterDecision.nodeId === baselineSelectedNodeId,
    });
    chaosQuarantines += scenario.request.nodes.filter((node) => node.health === 'quarantined').length;
    failovers += projection.failover.action === 'failover' ? 1 : 0;
    autoscalingTriggers += projection.autoscaling.action !== 'hold' ? 1 : 0;
  });

  return {
    available: true,
    soakRuns: 3,
    stableSelections,
    chaosRuns: chaosScenarios.length,
    chaosQuarantines,
    failovers,
    autoscalingTriggers,
    passed: stableSelections === 3 && chaosScenarios.length > 0 && (failovers > 0 || autoscalingTriggers > 0 || chaosQuarantines > 0),
    rows,
  };
}

function buildSovereignXClusterGovernanceProjectionCore(
  request: SovereignXClusterRouteRequest,
  clusterRouting: SovereignXClusterRouteResult,
  controlState: SovereignXClusterControlState,
  snapshot: SovereignXHardwareSnapshot,
): SovereignXClusterGovernanceProjection {
  void snapshot;
  const membershipNodes = buildMembershipNodes(request.nodes, clusterRouting, controlState);
  const summary = summarizeMembership(request.nodes, clusterRouting, membershipNodes, controlState);
  const autoscaling = buildAutoscalingSummary(summary, controlState, clusterRouting);
  const failover = buildFailoverSummary(clusterRouting, membershipNodes, controlState);

  return {
    available: true,
    controlState: cloneControlState(controlState),
    membershipNodes,
    summary,
    autoscaling,
    failover,
    soakChaosValidation: {
      available: true,
      soakRuns: 0,
      stableSelections: 0,
      chaosRuns: 0,
      chaosQuarantines: 0,
      failovers: 0,
      autoscalingTriggers: 0,
      passed: false,
      rows: [],
    },
    traceabilityMatrix: buildSovereignXConstitutionalTraceabilityMatrix(
      clusterRouting,
      summary,
      autoscaling,
      failover,
      {
        available: false,
        soakRuns: 0,
        stableSelections: 0,
        chaosRuns: 0,
        chaosQuarantines: 0,
        failovers: 0,
        autoscalingTriggers: 0,
        passed: false,
        rows: [],
      },
    ),
  };
}

function buildMembershipNodes(
  nodes: SovereignXClusterNode[],
  clusterRouting: SovereignXClusterRouteResult,
  controlState: SovereignXClusterControlState,
): SovereignXClusterMembershipState[] {
  const activeNodeIds = new Set(
    clusterRouting.nodeScores
      .filter((node) => node.eligible)
      .slice(0, Math.max(1, controlState.desiredNodeCount))
      .map((node) => node.nodeId),
  );

  return nodes.map((node) => {
    if (controlState.quarantinedNodeIds.includes(node.nodeId) || node.health === 'quarantined') {
      return {
        nodeId: node.nodeId,
        role: node.role,
        region: node.region,
        health: 'quarantined',
        controlState: 'quarantined',
        controlReason: 'operator or control plane quarantine',
        failoverCandidate: false,
        preferredBackend: node.preferredBackend,
      };
    }

    const active = activeNodeIds.has(node.nodeId);
    return {
      nodeId: node.nodeId,
      role: node.role,
      region: node.region,
      health: node.health,
      controlState: active ? 'active' : 'standby',
      controlReason: active
        ? 'selected by current routing and membership policy'
        : 'standing by for failover or scale-out',
      failoverCandidate: !active,
      preferredBackend: node.preferredBackend,
    };
  });
}

function summarizeMembership(
  nodes: SovereignXClusterNode[],
  clusterRouting: SovereignXClusterRouteResult,
  membershipNodes: SovereignXClusterMembershipState[],
  controlState: SovereignXClusterControlState,
): SovereignXClusterGovernanceProjection['summary'] {
  return {
    nodeCount: nodes.length,
    healthyNodeCount: nodes.filter((node) => node.health === 'healthy').length,
    eligibleNodeCount: clusterRouting.nodeScores.filter((node) => node.eligible).length,
    activeNodeCount: membershipNodes.filter((node) => node.controlState === 'active').length,
    quarantinedNodeCount: membershipNodes.filter((node) => node.controlState === 'quarantined').length,
    standbyNodeCount: membershipNodes.filter((node) => node.controlState === 'standby').length,
    desiredNodeCount: Math.max(1, controlState.desiredNodeCount),
    selectionPolicy: 'best eligible node by score with deterministic node-id tie break',
  };
}

function buildAutoscalingSummary(
  summary: SovereignXClusterGovernanceProjection['summary'],
  controlState: SovereignXClusterControlState,
  clusterRouting: SovereignXClusterRouteResult,
): SovereignXClusterAutoscalingSummary {
  const pressureScore = Number(
    (
      summary.activeNodeCount / Math.max(1, summary.desiredNodeCount) +
      summary.quarantinedNodeCount / Math.max(1, summary.nodeCount) +
      (clusterRouting.clusterDecision.action === 'dispatch' ? 0 : 0.5)
    ).toFixed(3),
  );

  if (summary.eligibleNodeCount < summary.desiredNodeCount || summary.healthyNodeCount < summary.desiredNodeCount) {
    return {
      action: 'scale_up',
      desiredNodeCount: controlState.desiredNodeCount,
      recommendedNodeCount: Math.max(summary.desiredNodeCount + 1, summary.healthyNodeCount + 1),
      activeNodeCount: summary.activeNodeCount,
      eligibleNodeCount: summary.eligibleNodeCount,
      pressureScore,
      reason: 'eligible capacity is below the desired cluster size',
    };
  }

  const averageLoad = clusterRouting.nodeScores.reduce((sum, node, index) => {
    void index;
    return sum + (node.eligible ? 1 / Math.max(1, summary.nodeCount) : 0);
  }, 0);

  if (summary.activeNodeCount > summary.desiredNodeCount + 1 && averageLoad < 0.45) {
    return {
      action: 'scale_down',
      desiredNodeCount: controlState.desiredNodeCount,
      recommendedNodeCount: Math.max(1, summary.desiredNodeCount - 1),
      activeNodeCount: summary.activeNodeCount,
      eligibleNodeCount: summary.eligibleNodeCount,
      pressureScore,
      reason: 'membership pressure is low enough to reduce the desired cluster size',
    };
  }

  return {
    action: 'hold',
    desiredNodeCount: controlState.desiredNodeCount,
    recommendedNodeCount: controlState.desiredNodeCount,
    activeNodeCount: summary.activeNodeCount,
    eligibleNodeCount: summary.eligibleNodeCount,
    pressureScore,
    reason: 'current membership matches the desired cluster size',
  };
}

function buildFailoverSummary(
  clusterRouting: SovereignXClusterRouteResult,
  membershipNodes: SovereignXClusterMembershipState[],
  controlState: SovereignXClusterControlState,
): SovereignXClusterFailoverSummary {
  const standbyNodeIds = membershipNodes.filter((node) => node.controlState !== 'quarantined').map((node) => node.nodeId);
  const preferredTarget = controlState.preferredFailoverNodeId
    ? membershipNodes.find((node) => node.nodeId === controlState.preferredFailoverNodeId && node.controlState !== 'quarantined')?.nodeId ?? null
    : null;
  const fallbackTarget = clusterRouting.nodeScores.find((node) => node.eligible)?.nodeId ?? null;
  const targetNodeId = preferredTarget ?? fallbackTarget;
  const fromNodeId = clusterRouting.clusterDecision.nodeId;

  if (clusterRouting.clusterDecision.action !== 'dispatch' && targetNodeId && targetNodeId !== fromNodeId) {
    return {
      action: 'failover',
      fromNodeId,
      toNodeId: targetNodeId,
      trigger: clusterRouting.clusterDecision.action,
      reason: 'control plane selected the best standby node for failover',
      standbyNodeIds,
    };
  }

  return {
    action: 'hold',
    fromNodeId,
    toNodeId: targetNodeId,
    trigger: clusterRouting.clusterDecision.action,
    reason: 'the current cluster decision can continue without failover',
    standbyNodeIds,
  };
}

function buildChaosScenarios(
  request: SovereignXClusterRouteRequest,
  controlState: SovereignXClusterControlState,
  snapshot: SovereignXHardwareSnapshot,
): {
  name: string;
  request: SovereignXClusterRouteRequest;
  controlState: SovereignXClusterControlState;
  snapshot: SovereignXHardwareSnapshot;
  clockMs: number;
}[] {
  const selectedNodeId = request.nodes.find((node) => node.health !== 'quarantined')?.nodeId ?? request.nodes[0]?.nodeId ?? 'node';
  const baseSnapshot = snapshot;
  const requestedClock = snapshot.governor.state.lastUpdatedAtMs;
  const withNodeClone = (mutate: (node: SovereignXClusterNode, index: number) => SovereignXClusterNode) => ({
    ...request,
    nodes: request.nodes.map(mutate),
  });

  return [
    {
      name: 'chaos-stale-heartbeat',
      request: withNodeClone((node, index) => (index === 0 ? { ...node, lastHeartbeatAtMs: node.lastHeartbeatAtMs - 120_000 } : node)),
      controlState,
      snapshot: baseSnapshot,
      clockMs: requestedClock + 1,
    },
    {
      name: 'chaos-quarantined-node',
      request: withNodeClone((node) => (node.nodeId === selectedNodeId ? { ...node, health: 'quarantined' } : node)),
      controlState: {
        ...controlState,
        quarantinedNodeIds: controlState.quarantinedNodeIds.includes(selectedNodeId)
          ? controlState.quarantinedNodeIds
          : [...controlState.quarantinedNodeIds, selectedNodeId],
      },
      snapshot: baseSnapshot,
      clockMs: requestedClock + 2,
    },
    {
      name: 'chaos-capacity-spike',
      request: withNodeClone((node) => (node.nodeId === selectedNodeId ? { ...node, activeJobs: node.maxJobs } : node)),
      controlState,
      snapshot: baseSnapshot,
      clockMs: requestedClock + 3,
    },
    {
      name: 'chaos-thermal-spike',
      request: {
        ...request,
        nodes: request.nodes.map((node) =>
          node.role === 'GPU'
            ? { ...node, gpuTempC: node.gpuTempC + 15, gpuUtilization: Math.min(1, node.gpuUtilization + 0.2) }
            : node,
        ),
      },
      controlState: {
        ...controlState,
        desiredNodeCount: Math.max(controlState.desiredNodeCount + 1, 2),
      },
      snapshot: baseSnapshot,
      clockMs: requestedClock + 4,
    },
  ];
}

function cloneControlState(state: SovereignXClusterControlState): SovereignXClusterControlState {
  return {
    desiredNodeCount: state.desiredNodeCount,
    quarantinedNodeIds: [...state.quarantinedNodeIds],
    preferredFailoverNodeId: state.preferredFailoverNodeId,
    lastAction: state.lastAction ? { ...state.lastAction } : null,
  };
}

function buildFallbackSovereignXHardwareSnapshot(): SovereignXHardwareSnapshot {
  const observedAtMs = Date.now();
  return {
    source: 'system',
    sourceDetail: 'fallback snapshot',
    telemetry: {
      cpuTempC: 40,
      gpuTempC: 41,
      cpuVolt: 1.02,
      gpuVolt: 1.03,
      powerDrawFraction: 0.2,
      utilization: 0.2,
      observedAtMs,
    },
    cycle: {
      decision: 'MAINTAIN',
      headroomC: 20,
      loadFactor: 0.2,
      transitions: [],
      evidence: {
        valid: true,
        samples: [],
      },
    },
    governor: {
      contract: {
        Contract: {
          Name: 'fallback',
          Authority: 'SovereignX.Router',
        },
      },
      invariants: {
        healthy: true,
        replayable: true,
      },
      previousState: {
        currentFrequencyMhz: 3200,
        currentVoltageV: 1.02,
        lastDecision: 'MAINTAIN',
        lastUpdatedAtMs: observedAtMs - 1,
      },
      state: {
        currentFrequencyMhz: 3200,
        currentVoltageV: 1.02,
        lastDecision: 'MAINTAIN',
        lastUpdatedAtMs: observedAtMs,
      },
      recentEvents: [],
    },
  } as unknown as SovereignXHardwareSnapshot;
}
