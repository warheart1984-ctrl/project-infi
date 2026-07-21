import { mapBackend } from './engineBridge.js';
import type {
  GovernanceLimits,
  RouteDecision,
  RouteEvaluation,
  RuntimeStats,
  WorkItem,
} from './types.js';
import type { SovereignXEngineBackend } from './engineBridge.js';
import { SovereignXRouter } from './SovereignXRouter.js';

export type SovereignXClusterNodeRole = 'CPU' | 'GPU' | 'MIXED';
export type SovereignXClusterNodeHealth = 'healthy' | 'degraded' | 'quarantined';

export interface SovereignXClusterNode {
  nodeId: string;
  role: SovereignXClusterNodeRole;
  region: string;
  maxJobs: number;
  activeJobs: number;
  cpuUtilization: number;
  gpuUtilization: number;
  gpuTempC: number;
  lastHeartbeatAtMs: number;
  health: SovereignXClusterNodeHealth;
  preferredBackend?: Exclude<SovereignXEngineBackend, 'cpu'>;
}

export interface SovereignXClusterNodeScore {
  nodeId: string;
  role: SovereignXClusterNodeRole;
  eligible: boolean;
  score: number;
  reasons: string[];
}

export interface SovereignXClusterRouteRequest {
  workItem: WorkItem;
  runtime: RuntimeStats;
  limits: GovernanceLimits;
  nodes: SovereignXClusterNode[];
  preferredGpuBackend?: Exclude<SovereignXEngineBackend, 'cpu'>;
  hardwareEvidence?: SovereignXHardwareEvidenceContext;
}

export interface SovereignXHardwareEvidenceContext {
  benchmarkArtifactIds: string[];
  replayArtifactIds: string[];
  preferredRoute?: 'cpu' | 'gpu' | 'mixed';
  confidence?: number;
}

export interface SovereignXClusterRouteDecision {
  action: 'dispatch' | 'delay' | 'drop';
  nodeId: string | null;
  nodeRole: SovereignXClusterNodeRole | null;
  backend: SovereignXEngineBackend | 'delay' | 'drop';
  reason: string;
}

export interface SovereignXClusterRouteResult {
  routeEvaluation: RouteEvaluation;
  clusterDecision: SovereignXClusterRouteDecision;
  selectedNode: SovereignXClusterNode | null;
  alternateNodes: SovereignXClusterNodeScore[];
  nodeScores: SovereignXClusterNodeScore[];
  hardwareEvidenceRefs: string[];
  summary: {
    nodeCount: number;
    healthyNodeCount: number;
    eligibleNodeCount: number;
    selectionPolicy: string;
  };
}

export interface SovereignXClusterRoutingOptions {
  clock?: () => number;
  maxHeartbeatAgeMs?: number;
}

export function routeSovereignXClusterWork(
  router: SovereignXRouter,
  request: SovereignXClusterRouteRequest,
  options: SovereignXClusterRoutingOptions = {},
): SovereignXClusterRouteResult {
  const routeEvaluation = router.evaluate(request.workItem, request.runtime, request.limits);
  const backend = mapBackend(routeEvaluation, request.preferredGpuBackend);
  const now = options.clock?.() ?? Date.now();
  const maxHeartbeatAgeMs = options.maxHeartbeatAgeMs ?? 30_000;
  const hardwareEvidenceRefs = [
    ...(request.hardwareEvidence?.benchmarkArtifactIds ?? []),
    ...(request.hardwareEvidence?.replayArtifactIds ?? []),
  ];
  const nodeScores = request.nodes
    .map((node) => scoreNode(node, routeEvaluation.localDecision.target, now, maxHeartbeatAgeMs, request.hardwareEvidence))
    .sort((left, right) => right.score - left.score || left.nodeId.localeCompare(right.nodeId));
  const eligibleNodeScores = nodeScores.filter((node) => node.eligible);
  const selectedNodeScore = eligibleNodeScores[0] ?? null;
  const selectedNode = selectedNodeScore
    ? request.nodes.find((node) => node.nodeId === selectedNodeScore.nodeId) ?? null
    : null;

  if (routeEvaluation.effectiveDecision.target === 'DROP') {
    return {
      routeEvaluation,
      clusterDecision: {
        action: 'drop',
        nodeId: null,
        nodeRole: null,
        backend: 'drop',
        reason: 'cluster work was dropped by the local governance layer',
      },
      selectedNode: null,
      alternateNodes: eligibleNodeScores.slice(1),
      nodeScores,
      hardwareEvidenceRefs,
      summary: summarizeCluster(request.nodes, nodeScores),
    };
  }

  if (routeEvaluation.effectiveDecision.target === 'DELAY' || !selectedNode) {
    return {
      routeEvaluation,
      clusterDecision: {
        action: 'delay',
        nodeId: null,
        nodeRole: null,
        backend: 'delay',
        reason: selectedNode ? 'cluster routing deferred by governance' : 'no eligible nodes available for dispatch',
      },
      selectedNode: null,
      alternateNodes: eligibleNodeScores.slice(1),
      nodeScores,
      hardwareEvidenceRefs,
      summary: summarizeCluster(request.nodes, nodeScores),
    };
  }

  return {
    routeEvaluation,
    clusterDecision: {
      action: 'dispatch',
      nodeId: selectedNode.nodeId,
      nodeRole: selectedNode.role,
      backend,
      reason: buildDispatchReason(routeEvaluation.localDecision.target, selectedNode),
    },
    selectedNode,
    alternateNodes: eligibleNodeScores.slice(1),
    nodeScores,
    hardwareEvidenceRefs,
    summary: summarizeCluster(request.nodes, nodeScores),
  };
}

function scoreNode(
  node: SovereignXClusterNode,
  target: RouteDecision['target'],
  now: number,
  maxHeartbeatAgeMs: number,
  hardwareEvidence?: SovereignXHardwareEvidenceContext,
): SovereignXClusterNodeScore {
  const reasons: string[] = [];
  const ageMs = now - node.lastHeartbeatAtMs;
  let eligible = node.health !== 'quarantined' && node.activeJobs < node.maxJobs && ageMs <= maxHeartbeatAgeMs;

  if (node.health === 'degraded') {
    reasons.push('node is degraded');
  }
  if (node.health === 'quarantined') {
    reasons.push('node is quarantined');
  }
  if (ageMs > maxHeartbeatAgeMs) {
    reasons.push(`heartbeat age ${ageMs}ms exceeds ${maxHeartbeatAgeMs}ms`);
  }
  if (node.activeJobs >= node.maxJobs) {
    reasons.push('node is at capacity');
  }

  const roleMatches =
    target === 'CPU'
      ? node.role === 'CPU' || node.role === 'MIXED'
      : target === 'GPU'
        ? node.role === 'GPU' || node.role === 'MIXED'
        : false;
  if (!roleMatches) {
    eligible = false;
    reasons.push(`node role ${node.role} is incompatible with ${target}`);
  }
  if (target === 'DROP' || target === 'DELAY') {
    eligible = false;
  }

  let score = 100;
  score -= node.activeJobs * 13;
  score -= Math.round((node.activeJobs / Math.max(1, node.maxJobs)) * 20);
  score -= Math.min(30, Math.floor(ageMs / 1_000));
  if (node.health === 'degraded') {
    score -= 18;
  }
  if (node.health === 'quarantined') {
    score -= 100;
  }
  if (target === 'GPU') {
    score -= Math.max(0, node.gpuTempC - 72);
    score -= Math.round(node.gpuUtilization * 10);
  }
  if (target === 'CPU') {
    score -= Math.round(node.cpuUtilization * 10);
  }

  if (node.role === target) {
    score += 30;
  } else if (node.role === 'MIXED') {
    score += 8;
  }

  if (hardwareEvidence?.preferredRoute === 'gpu' && target === 'GPU') {
    score += 7 * clampHardwareEvidenceConfidence(hardwareEvidence.confidence);
    reasons.push('hardware evidence favors GPU route');
  }
  if (hardwareEvidence?.preferredRoute === 'cpu' && target === 'CPU') {
    score += 7 * clampHardwareEvidenceConfidence(hardwareEvidence.confidence);
    reasons.push('hardware evidence favors CPU route');
  }
  if (hardwareEvidence?.replayArtifactIds?.length) {
    score += Math.min(4, hardwareEvidence.replayArtifactIds.length);
    reasons.push(`replay evidence refs: ${hardwareEvidence.replayArtifactIds.join(', ')}`);
  }
  if (hardwareEvidence?.benchmarkArtifactIds?.length) {
    score += Math.min(4, hardwareEvidence.benchmarkArtifactIds.length);
    reasons.push(`benchmark evidence refs: ${hardwareEvidence.benchmarkArtifactIds.join(', ')}`);
  }

  return {
    nodeId: node.nodeId,
    role: node.role,
    eligible,
    score: Number(score.toFixed(2)),
    reasons,
  };
}

function clampHardwareEvidenceConfidence(value: number | undefined): number {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 0.5;
  }
  return Math.max(0, Math.min(1, value));
}

function summarizeCluster(nodes: SovereignXClusterNode[], nodeScores: SovereignXClusterNodeScore[]): SovereignXClusterRouteResult['summary'] {
  return {
    nodeCount: nodes.length,
    healthyNodeCount: nodes.filter((node) => node.health === 'healthy').length,
    eligibleNodeCount: nodeScores.filter((node) => node.eligible).length,
    selectionPolicy: 'best eligible node by score with deterministic node-id tie break',
  };
}

function buildDispatchReason(target: RouteDecision['target'], node: SovereignXClusterNode): string {
  if (target === 'GPU' && node.preferredBackend) {
    return `routed to ${node.nodeId} on ${node.region} using ${node.preferredBackend} after GPU governance`;
  }
  return `routed to ${node.nodeId} on ${node.region} after ${target.toLowerCase()} governance`;
}
