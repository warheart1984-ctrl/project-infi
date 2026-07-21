import os from 'node:os';

import type { SovereignXClusterRouteResult, SovereignXClusterNode, SovereignXClusterNodeRole } from '@aaes-os/sovereignx-router';
import type { SovereignXHardwareSnapshot } from './SovereignXHardwareTelemetryAdapter.js';

export type HardwareBackend = 'local' | 'remote' | 'gpu-cluster' | 'cpu-cluster';
export type HardwareQuarantineState = 'none' | 'soft' | 'hard';
export type HardwareRoute = 'cpu' | 'gpu' | 'mixed';

export interface HardwareNodeSnapshot {
  nodeId: string;
  backend: HardwareBackend;
  cpuUtilization: number;
  gpuUtilization: number;
  cpuTempC: number | null;
  gpuTempC: number | null;
  voltageMv: number | null;
  thermalWarnings: string[];
  quarantineState: HardwareQuarantineState;
  memoryPressure: number;
  source: SovereignXHardwareSnapshot['source'];
  sourceDetail: string;
  lastObservedAtMs: number;
  selected: boolean;
  routePreference: HardwareRoute;
}

export interface HardwareStatusStrip {
  throttlingEvents: number;
  quarantinedNodes: number;
  averageUtilization: number;
  averageCpuTempC: number;
  averageGpuTempC: number;
  averageMemoryPressure: number;
  eligibleNodes: number;
  selectedNodes: number;
}

export interface BenchmarkSpec {
  id: string;
  name: string;
  description?: string;
  workloadType: 'llm' | 'api' | 'batch' | 'custom';
  parameters: Record<string, unknown>;
  targetRoutes: HardwareRoute[];
}

export interface BenchmarkMetrics {
  latencyP50Ms: number;
  latencyP95Ms: number;
  latencyP99Ms: number;
  throughputPerSec: number;
  gpuUtilizationAvg: number;
  cpuUtilizationAvg: number;
  thermalHeadroomPct: number;
  memoryPressureAvg: number;
  errorRatePct: number;
  throttleCount: number;
  failoverCount: number;
  costPerRequestUsd: number;
  costPer1kTokensUsd?: number;
}

export interface BenchmarkMetricsDelta {
  latencyP50Ms: number;
  latencyP95Ms: number;
  latencyP99Ms: number;
  throughputPerSec: number;
  gpuUtilizationAvg: number;
  cpuUtilizationAvg: number;
  thermalHeadroomPct: number;
  memoryPressureAvg: number;
  errorRatePct: number;
  throttleCount: number;
  failoverCount: number;
  costPerRequestUsd: number;
  costPer1kTokensUsd?: number;
}

export interface HardwareReplayComparison {
  workloadId: string;
  currentRoute: 'cpu' | 'gpu';
  counterfactualRoute: 'cpu' | 'gpu';
  currentMetrics: BenchmarkMetrics;
  counterfactualMetrics: BenchmarkMetrics;
  delta: BenchmarkMetricsDelta;
}

export interface HardwareBenchmarkRunArtifact {
  artifactType: 'HardwareBenchmarkArtifact';
  benchmarkSpec: BenchmarkSpec;
  route: HardwareRoute;
  metrics: BenchmarkMetrics;
  evidenceRefs: string[];
}

export interface HardwareReplayArtifact {
  artifactType: 'HardwareReplayEvidenceArtifact';
  workloadId: string;
  currentRoute: 'cpu' | 'gpu';
  counterfactualRoute: 'cpu' | 'gpu';
  comparison: HardwareReplayComparison;
  evidenceRefs: string[];
}

export interface HardwareConsoleSummary {
  available: boolean;
  generatedAtMs: number;
  source: SovereignXHardwareSnapshot['source'];
  sourceDetail: string;
  nodes: HardwareNodeSnapshot[];
  statusStrip: HardwareStatusStrip;
  benchmarkSpecs: BenchmarkSpec[];
  latestBenchmarkRun: HardwareBenchmarkRunArtifact | null;
  latestReplayComparison: HardwareReplayArtifact | null;
  recentBenchmarkRuns: HardwareBenchmarkRunArtifact[];
  recentReplayComparisons: HardwareReplayArtifact[];
  hardwareEvidenceRefs: string[];
  clusterDecision: SovereignXClusterRouteResult['clusterDecision'];
  clusterSummary: SovereignXClusterRouteResult['summary'];
}

export interface HardwareConsoleInputs {
  snapshot: SovereignXHardwareSnapshot;
  clusterRouting: SovereignXClusterRouteResult;
  benchmarkRuns: HardwareBenchmarkRunArtifact[];
  replayArtifacts: HardwareReplayArtifact[];
}

export function buildHardwareConsoleSummary(input: HardwareConsoleInputs): HardwareConsoleSummary {
  const nodes = buildHardwareNodeSnapshots(input.snapshot, input.clusterRouting);
  const statusStrip = buildHardwareStatusStrip(nodes, input.clusterRouting);
  const benchmarkSpecs = buildHardwareBenchmarkCatalog();
  const latestBenchmarkRun = input.benchmarkRuns[input.benchmarkRuns.length - 1] ?? null;
  const latestReplayComparison = input.replayArtifacts[input.replayArtifacts.length - 1] ?? null;

  return {
    available: true,
    generatedAtMs: input.snapshot.telemetry.observedAtMs ?? input.snapshot.governor.state.lastUpdatedAtMs,
    source: input.snapshot.source,
    sourceDetail: input.snapshot.sourceDetail,
    nodes,
    statusStrip,
    benchmarkSpecs,
    latestBenchmarkRun,
    latestReplayComparison,
    recentBenchmarkRuns: input.benchmarkRuns.slice(-5).reverse(),
    recentReplayComparisons: input.replayArtifacts.slice(-5).reverse(),
    hardwareEvidenceRefs: [
      ...(latestBenchmarkRun ? [`benchmark:${latestBenchmarkRun.benchmarkSpec.id}:${latestBenchmarkRun.route}`] : []),
      ...(latestReplayComparison ? [`replay:${latestReplayComparison.workloadId}`] : []),
    ],
    clusterDecision: input.clusterRouting.clusterDecision,
    clusterSummary: input.clusterRouting.summary,
  };
}

export function buildHardwareNodeSnapshots(
  snapshot: SovereignXHardwareSnapshot,
  clusterRouting: SovereignXClusterRouteResult,
): HardwareNodeSnapshot[] {
  const observedAtMs = snapshot.telemetry.observedAtMs ?? snapshot.governor.state.lastUpdatedAtMs;
  const selectedNodeId = clusterRouting.clusterDecision.nodeId;
  return clusterRouting.nodeScores.map((score, index) => {
    const node = clusterRouting.selectedNode?.nodeId === score.nodeId
      ? clusterRouting.selectedNode
      : null;
    const backend = node?.role === 'CPU'
      ? 'cpu-cluster'
      : node?.role === 'GPU'
        ? 'gpu-cluster'
        : node?.role === 'MIXED'
          ? 'remote'
          : index % 2 === 0
            ? 'cpu-cluster'
            : 'gpu-cluster';
    const cpuUtilization = node ? node.cpuUtilization * 100 : roundTo(48 + index * 9 + snapshot.telemetry.utilization * 8, 1);
    const gpuUtilization = node ? node.gpuUtilization * 100 : roundTo(36 + index * 11 + snapshot.telemetry.utilization * 12, 1);
    const cpuTempC = node ? roundTo(Math.max(0, snapshot.telemetry.cpuTempC - index * 1.4), 1) : null;
    const gpuTempC = node ? roundTo(Math.max(0, snapshot.telemetry.gpuTempC - index * 1.2), 1) : null;
    const voltageMv = node ? roundTo((snapshot.telemetry.cpuVolt + snapshot.telemetry.gpuVolt) * 500, 0) : null;
    const thermalWarnings = buildThermalWarnings(snapshot, node?.role ?? score.role, node?.health ?? 'healthy');
    const quarantineState: HardwareQuarantineState = node?.health === 'quarantined'
      ? 'hard'
      : node?.health === 'degraded'
        ? 'soft'
        : 'none';

    return {
      nodeId: node?.nodeId ?? score.nodeId,
      backend,
      cpuUtilization: roundTo(cpuUtilization, 1),
      gpuUtilization: roundTo(gpuUtilization, 1),
      cpuTempC,
      gpuTempC,
      voltageMv,
      thermalWarnings,
      quarantineState,
      memoryPressure: roundTo(memoryPressure(snapshot), 1),
      source: snapshot.source,
      sourceDetail: snapshot.sourceDetail,
      lastObservedAtMs: observedAtMs,
      selected: selectedNodeId === score.nodeId,
      routePreference: clusterRouting.routeEvaluation.effectiveDecision.target === 'GPU'
        ? 'gpu'
        : clusterRouting.routeEvaluation.effectiveDecision.target === 'CPU'
          ? 'cpu'
          : 'mixed',
    };
  });
}

export function buildHardwareStatusStrip(
  nodes: HardwareNodeSnapshot[],
  clusterRouting: SovereignXClusterRouteResult,
): HardwareStatusStrip {
  const quarantinedNodes = nodes.filter((node) => node.quarantineState !== 'none').length;
  const throttlingEvents = nodes.reduce((sum, node) => sum + node.thermalWarnings.length, 0);
  const averageUtilization = nodes.length > 0 ? roundTo(nodes.reduce((sum, node) => sum + ((node.cpuUtilization + node.gpuUtilization) / 2), 0) / nodes.length, 1) : 0;
  const averageCpuTempC = nodes.filter((node) => node.cpuTempC !== null).length > 0
    ? roundTo(nodes.reduce((sum, node) => sum + (node.cpuTempC ?? 0), 0) / nodes.filter((node) => node.cpuTempC !== null).length, 1)
    : 0;
  const averageGpuTempC = nodes.filter((node) => node.gpuTempC !== null).length > 0
    ? roundTo(nodes.reduce((sum, node) => sum + (node.gpuTempC ?? 0), 0) / nodes.filter((node) => node.gpuTempC !== null).length, 1)
    : 0;
  const averageMemoryPressure = nodes.length > 0 ? roundTo(nodes.reduce((sum, node) => sum + node.memoryPressure, 0) / nodes.length, 1) : 0;

  return {
    throttlingEvents,
    quarantinedNodes,
    averageUtilization,
    averageCpuTempC,
    averageGpuTempC,
    averageMemoryPressure,
    eligibleNodes: clusterRouting.summary.eligibleNodeCount,
    selectedNodes: clusterRouting.clusterDecision.nodeId ? 1 : 0,
  };
}

export function buildHardwareBenchmarkCatalog(): BenchmarkSpec[] {
  return [
    {
      id: 'llm-chat-128k',
      name: 'LLM chat 128k',
      description: 'Representative long-context chat workload with moderate concurrency.',
      workloadType: 'llm',
      parameters: {
        promptTokens: 12000,
        completionTokens: 1800,
        concurrency: 4,
      },
      targetRoutes: ['cpu', 'gpu', 'mixed'],
    },
    {
      id: 'api-burst-256',
      name: 'API burst 256',
      description: 'Throughput-sensitive burst of short request/response calls.',
      workloadType: 'api',
      parameters: {
        payloadBytes: 4096,
        concurrency: 32,
        durationSeconds: 30,
      },
      targetRoutes: ['cpu', 'gpu'],
    },
  ];
}

export function estimateHardwareBenchmarkMetrics(
  snapshot: SovereignXHardwareSnapshot,
  clusterRouting: SovereignXClusterRouteResult,
  spec: BenchmarkSpec,
  route: HardwareRoute,
): BenchmarkMetrics {
  const utilization = clamp(snapshot.telemetry.utilization, 0, 1);
  const power = clamp(snapshot.telemetry.powerDrawFraction, 0, 1);
  const baseLatency = spec.workloadType === 'llm' ? 420 : spec.workloadType === 'batch' ? 260 : 180;
  const routeBias = route === 'gpu' ? 0.78 : route === 'mixed' ? 0.9 : 1.08;
  const governanceBias = clusterRouting.clusterDecision.action === 'dispatch' ? 0.96 : clusterRouting.clusterDecision.action === 'delay' ? 1.12 : 1.18;
  const thermalPressure = clamp((snapshot.telemetry.gpuTempC - 55) / 35, 0, 1);
  const latencyP50Ms = roundTo(baseLatency * routeBias * (1 + utilization * 0.12 + thermalPressure * 0.08) * governanceBias, 1);
  const latencyP95Ms = roundTo(latencyP50Ms * 1.28, 1);
  const latencyP99Ms = roundTo(latencyP50Ms * 1.58, 1);
  const throughputPerSec = roundTo((1000 / Math.max(1, latencyP50Ms)) * (route === 'gpu' ? 1.45 : route === 'mixed' ? 1.18 : 1), 3);
  const gpuUtilizationAvg = roundTo(clamp(route === 'gpu' ? utilization * 100 : utilization * 62 + 12, 0, 100), 1);
  const cpuUtilizationAvg = roundTo(clamp(route === 'cpu' ? utilization * 100 : utilization * 58 + 16, 0, 100), 1);
  const thermalHeadroomPct = roundTo(clamp(100 - (route === 'gpu' ? snapshot.telemetry.gpuTempC : snapshot.telemetry.cpuTempC), 0, 100), 1);
  const memoryPressureAvg = roundTo(memoryPressure(snapshot), 1);
  const errorRatePct = roundTo(clamp((clusterRouting.clusterDecision.action === 'drop' ? 1.8 : 0.3) + thermalPressure * 0.7 + power * 0.2, 0, 5), 2);
  const throttleCount = Math.max(0, Math.round((thermalPressure + power) * 4));
  const failoverCount = clusterRouting.clusterDecision.action === 'dispatch' ? 0 : 1;
  const costPerRequestUsd = roundTo((route === 'gpu' ? 0.025 : route === 'mixed' ? 0.018 : 0.015) * (1 + utilization * 0.2 + thermalPressure * 0.15), 4);

  return {
    latencyP50Ms,
    latencyP95Ms,
    latencyP99Ms,
    throughputPerSec,
    gpuUtilizationAvg,
    cpuUtilizationAvg,
    thermalHeadroomPct,
    memoryPressureAvg,
    errorRatePct,
    throttleCount,
    failoverCount,
    costPerRequestUsd,
    costPer1kTokensUsd: spec.workloadType === 'llm' ? roundTo(costPerRequestUsd * 5.8, 4) : undefined,
  };
}

export function compareHardwareBenchmarkMetrics(
  currentMetrics: BenchmarkMetrics,
  counterfactualMetrics: BenchmarkMetrics,
): BenchmarkMetricsDelta {
  return {
    latencyP50Ms: roundTo(counterfactualMetrics.latencyP50Ms - currentMetrics.latencyP50Ms, 2),
    latencyP95Ms: roundTo(counterfactualMetrics.latencyP95Ms - currentMetrics.latencyP95Ms, 2),
    latencyP99Ms: roundTo(counterfactualMetrics.latencyP99Ms - currentMetrics.latencyP99Ms, 2),
    throughputPerSec: roundTo(counterfactualMetrics.throughputPerSec - currentMetrics.throughputPerSec, 3),
    gpuUtilizationAvg: roundTo(counterfactualMetrics.gpuUtilizationAvg - currentMetrics.gpuUtilizationAvg, 2),
    cpuUtilizationAvg: roundTo(counterfactualMetrics.cpuUtilizationAvg - currentMetrics.cpuUtilizationAvg, 2),
    thermalHeadroomPct: roundTo(counterfactualMetrics.thermalHeadroomPct - currentMetrics.thermalHeadroomPct, 2),
    memoryPressureAvg: roundTo(counterfactualMetrics.memoryPressureAvg - currentMetrics.memoryPressureAvg, 2),
    errorRatePct: roundTo(counterfactualMetrics.errorRatePct - currentMetrics.errorRatePct, 2),
    throttleCount: counterfactualMetrics.throttleCount - currentMetrics.throttleCount,
    failoverCount: counterfactualMetrics.failoverCount - currentMetrics.failoverCount,
    costPerRequestUsd: roundTo(counterfactualMetrics.costPerRequestUsd - currentMetrics.costPerRequestUsd, 4),
    costPer1kTokensUsd:
      typeof currentMetrics.costPer1kTokensUsd === 'number' && typeof counterfactualMetrics.costPer1kTokensUsd === 'number'
        ? roundTo(counterfactualMetrics.costPer1kTokensUsd - currentMetrics.costPer1kTokensUsd, 4)
        : undefined,
  };
}

export function buildHardwareReplayComparison(
  workloadId: string,
  currentRoute: 'cpu' | 'gpu',
  counterfactualRoute: 'cpu' | 'gpu',
  currentMetrics: BenchmarkMetrics,
  counterfactualMetrics: BenchmarkMetrics,
): HardwareReplayComparison {
  return {
    workloadId,
    currentRoute,
    counterfactualRoute,
    currentMetrics,
    counterfactualMetrics,
    delta: compareHardwareBenchmarkMetrics(currentMetrics, counterfactualMetrics),
  };
}

export function resolvePreferredHardwareRoute(clusterRouting: SovereignXClusterRouteResult): HardwareRoute {
  if (clusterRouting.routeEvaluation.effectiveDecision.target === 'GPU') {
    return 'gpu';
  }
  if (clusterRouting.routeEvaluation.effectiveDecision.target === 'CPU') {
    return 'cpu';
  }
  return 'mixed';
}

function buildThermalWarnings(
  snapshot: SovereignXHardwareSnapshot,
  role: SovereignXClusterNodeRole | undefined,
  health: SovereignXClusterNode['health'],
): string[] {
  const warnings: string[] = [];
  if (snapshot.telemetry.cpuTempC >= 72) {
    warnings.push('CPU_THERMAL_HIGH');
  }
  if (snapshot.telemetry.gpuTempC >= 74) {
    warnings.push('GPU_THERMAL_HIGH');
  }
  if (snapshot.telemetry.powerDrawFraction >= 0.82) {
    warnings.push('POWER_DRAW_HIGH');
  }
  if (health === 'degraded') {
    warnings.push('NODE_DEGRADED');
  }
  if (health === 'quarantined') {
    warnings.push('NODE_QUARANTINED');
  }
  if (role === 'MIXED' && warnings.length === 0) {
    warnings.push('MIXED_BACKEND_MONITORED');
  }
  return warnings;
}

function memoryPressure(_snapshot: SovereignXHardwareSnapshot): number {
  const total = typeof process.memoryUsage === 'function' ? process.memoryUsage().rss : 0;
  const totalMem = os.totalmem();
  return totalMem > 0 ? clamp((total / totalMem) * 100, 0, 100) : 0;
}

function roundTo(value: number, digits: number): number {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}
