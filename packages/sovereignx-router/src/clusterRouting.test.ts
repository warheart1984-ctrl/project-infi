import { describe, expect, it } from 'vitest';

import {
  SovereignXRouter,
  validateSovereignXRouterProofSurface,
  type GovernanceLimits,
  type RuntimeStats,
  type WorkItem,
} from './index.js';
import { routeSovereignXClusterWork } from './clusterRouting.js';

const limits: GovernanceLimits = {
  maxGpuJobs: 2,
  maxCpuJobs: 8,
  maxConcurrentJobs: 4,
  maxGpuTempC: 80,
  maxVramBytes: 8_000_000_000,
  maxTokensPerAgentPerMin: 1_000,
  maxFlopsPerAgentPerMin: 1_000_000_000_000,
};

const runtime: RuntimeStats = {
  activeGpuJobs: 1,
  activeCpuJobs: 2,
  gpuUtil: 0.52,
  cpuUtil: 0.41,
  gpuTempC: 71,
  vramUsedBytes: 2_000_000_000,
  vramTotalBytes: 16_000_000_000,
};

function createRouter() {
  const router = new SovereignXRouter({ clock: () => 1_700_000_000_000 });
  router.registerIntent({
    id: 'intent-llm',
    domain: 'llm_step',
    rules: 'llm steps are allowed on GPU or CPU when governed',
    allowedTargets: ['GPU', 'CPU'],
    maxTokensPerAgentPerMin: 512,
    maxFlopsPerAgentPerMin: 500_000_000_000,
  });
  return router;
}

describe('SovereignX cluster routing', () => {
  const workItem: WorkItem = {
    id: 'cluster-work-1',
    agentId: 'agent-cluster',
    kind: 'llm_step',
    intentId: 'intent-llm',
    costEstimateTokens: 128,
    costEstimateFlops: 120_000_000_000,
    costEstimateMs: 40,
    priority: 3,
  };

  it('routes work to the best eligible cluster node', () => {
    const router = createRouter();
    const result = routeSovereignXClusterWork(
      router,
      {
        workItem,
        runtime,
        limits,
        nodes: [
          {
            nodeId: 'cpu-a',
            role: 'CPU',
            region: 'us-east-1',
            maxJobs: 6,
            activeJobs: 4,
            cpuUtilization: 0.48,
            gpuUtilization: 0.12,
            gpuTempC: 64,
            lastHeartbeatAtMs: 1_700_000_000_000 - 1_000,
            health: 'healthy',
          },
          {
            nodeId: 'gpu-a',
            role: 'GPU',
            region: 'us-east-1',
            maxJobs: 4,
            activeJobs: 1,
            cpuUtilization: 0.22,
            gpuUtilization: 0.31,
            gpuTempC: 69,
            lastHeartbeatAtMs: 1_700_000_000_000 - 500,
            health: 'healthy',
            preferredBackend: 'opencl',
          },
          {
            nodeId: 'mixed-a',
            role: 'MIXED',
            region: 'us-west-2',
            maxJobs: 5,
            activeJobs: 0,
            cpuUtilization: 0.18,
            gpuUtilization: 0.17,
            gpuTempC: 63,
            lastHeartbeatAtMs: 1_700_000_000_000 - 250,
            health: 'healthy',
            preferredBackend: 'vulkan',
          },
        ],
        preferredGpuBackend: 'opencl',
      },
      { clock: () => 1_700_000_000_500 },
    );

    expect(result.routeEvaluation.effectiveDecision.target).toBe('GPU');
    expect(result.clusterDecision.action).toBe('dispatch');
    expect(result.clusterDecision.nodeId).toBe('gpu-a');
    expect(result.clusterDecision.backend).toBe('opencl');
    expect(result.summary.eligibleNodeCount).toBe(2);
    expect(result.alternateNodes.map((node) => node.nodeId)).toEqual(['mixed-a']);
  });

  it('delays routing when no eligible node can host the work', () => {
    const router = createRouter();
    const result = routeSovereignXClusterWork(
      router,
      {
        workItem,
        runtime,
        limits,
        nodes: [
          {
            nodeId: 'cpu-b',
            role: 'CPU',
            region: 'us-east-1',
            maxJobs: 1,
            activeJobs: 1,
            cpuUtilization: 0.9,
            gpuUtilization: 0.1,
            gpuTempC: 64,
            lastHeartbeatAtMs: 1_700_000_000_000 - 50_000,
            health: 'quarantined',
          },
        ],
      },
      { clock: () => 1_700_000_000_500, maxHeartbeatAgeMs: 10_000 },
    );

    expect(result.clusterDecision.action).toBe('delay');
    expect(result.clusterDecision.reason).toContain('no eligible nodes');
    expect(result.selectedNode).toBeNull();
    expect(result.summary.eligibleNodeCount).toBe(0);
  });
});

describe('SovereignX proof surface', () => {
  it('validates the router proof surface after cluster routing evidence is included', () => {
    const validation = validateSovereignXRouterProofSurface();

    expect(validation.passed).toBe(true);
    expect(validation.issues.every((issue) => issue.severity !== 'error')).toBe(true);
  });
});
