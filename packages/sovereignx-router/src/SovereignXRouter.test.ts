import { describe, expect, it } from 'vitest';

import {
  SovereignXRouter,
  buildRelationshipTrustPacket,
  invokeSovereignXLlmInference,
  mapBackend,
  routeSovereignXLlmInference,
  applyTrustToCandidateModel,
  compileRoutingDsl,
  parseRoutingDsl,
  validateSovereignXRouterProofSurface,
  type GovernanceLimits,
  type CandidateModel,
  type RuntimeStats,
  type WorkItem,
} from './index.js';
import { buildRouteDecisionArtifact } from '../dist/index.js';

const limits: GovernanceLimits = {
  maxGpuJobs: 2,
  maxCpuJobs: 8,
  maxConcurrentJobs: 4,
  maxGpuTempC: 80,
  maxVramBytes: 8_000_000_000,
  maxTokensPerAgentPerMin: 1_000,
  maxFlopsPerAgentPerMin: 1_000_000_000_000,
};

const baseRuntime: RuntimeStats = {
  activeGpuJobs: 1,
  activeCpuJobs: 1,
  gpuUtil: 0.5,
  cpuUtil: 0.3,
  gpuTempC: 72,
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
  router.registerIntent({
    id: 'intent-tool',
    domain: 'tool_call',
    rules: 'tool calls must stay on CPU governance path',
    allowedTargets: ['CPU'],
    maxTokensPerAgentPerMin: 64,
    maxFlopsPerAgentPerMin: 10_000_000,
  });
  return router;
}

function createSignedTrustPacket(score: number, band: 'low' | 'medium' | 'high', governanceLevel: 'basic' | 'enhanced' | 'full' = 'full') {
  const packet = buildRelationshipTrustPacket({
    relationshipId: `relationship-${band}-${score.toFixed(2)}`,
    revision: 1,
    subjectId: 'org-1',
    objectId: 'router-x',
    relationshipKind: 'trust',
    governanceLevel,
    authorityChain: ['steward-1', 'delegate-1', 'kernel-1'],
    trust: {
      score,
      band,
      evidenceIds: ['evidence-1', 'evidence-2', 'evidence-3'],
      authority: { stewardId: 'steward-1' },
      provenance: { originSystem: 'relationship-ledger', method: 'assertion' },
    },
    ledgerEntryId: 'ledger-1',
    receiptId: 'receipt-1',
    capturedAt: '2026-07-11T00:00:00.000Z',
  });
    return {
      ...packet,
      signature: {
        algorithm: 'HMAC-SHA256',
        signer: 'unit-test-steward',
        signedAt: '2026-07-11T00:00:00.000Z',
        value: `signature-${band}-${score.toFixed(2)}`,
      },
    };
  }

describe('SovereignXRouter', () => {
  const workItem: WorkItem = {
    id: 'work-1',
    agentId: 'agent-7',
    kind: 'llm_step',
    intentId: 'intent-llm',
    costEstimateTokens: 128,
    costEstimateFlops: 120_000_000_000,
    costEstimateMs: 40,
    priority: 3,
  };

  it('routes governed llm work to GPU when safe', () => {
    const router = createRouter();
    const evaluation = router.evaluate(workItem, baseRuntime, limits);

    expect(evaluation.localDecision.target).toBe('GPU');
    expect(evaluation.effectiveDecision.target).toBe('GPU');
    expect(evaluation.evidence.workItemId).toBe('work-1');
    expect(router.listEvidence()).toHaveLength(1);
  });

  it('falls back to CPU when the GPU is too hot', () => {
    const router = createRouter();
    const hotRuntime = { ...baseRuntime, gpuTempC: 91 };
    const evaluation = router.evaluate(workItem, hotRuntime, limits);

    expect(evaluation.localDecision.target).toBe('CPU');
    expect(evaluation.effectiveDecision.target).toBe('DELAY');
    expect(evaluation.effectiveDecision.reason).toContain('CIEMS throttle');
  });

  it('delays work when the agent exceeds its budget', () => {
    const router = createRouter();
    const overloaded: WorkItem = { ...workItem, costEstimateTokens: 2_000 };
    const evaluation = router.evaluate(overloaded, baseRuntime, limits);

    expect(evaluation.localDecision.target).toBe('DELAY');
    expect(evaluation.effectiveDecision.target).toBe('DELAY');
    expect(evaluation.ciemsDecisions.some((decision) => decision.action === 'throttle')).toBe(true);
  });

  it('quarantines unregistered intents', () => {
    const router = createRouter();
    const unknownIntent: WorkItem = { ...workItem, intentId: 'intent-missing' };
    const evaluation = router.evaluate(unknownIntent, baseRuntime, limits);

    expect(evaluation.ciemsDecisions.some((decision) => decision.action === 'quarantine')).toBe(true);
    expect(evaluation.effectiveDecision.target).toBe('DROP');
  });

  it('keeps tool calls on the CPU path', () => {
    const router = createRouter();
    const toolItem: WorkItem = {
      id: 'work-2',
      agentId: 'agent-2',
      kind: 'tool_call',
      intentId: 'intent-tool',
      costEstimateTokens: 32,
      costEstimateFlops: 1_000_000,
    };

    const evaluation = router.evaluate(toolItem, baseRuntime, limits);

    expect(evaluation.localDecision.target).toBe('CPU');
    expect(evaluation.effectiveDecision.target).toBe('CPU');
  });

  it('maps llm work items into engine backend choices', () => {
    const router = createRouter();
    const routed = routeSovereignXLlmInference(
      router,
      {
        id: 'llm-work-1',
        agentId: 'agent-llm',
        intentId: 'intent-llm',
        prompt: 'hello sovereignx',
        promptTokens: 64,
        estimatedFlops: 10_000_000_000,
        maxTokens: 32,
        temperature: 0.15,
        preferredGpuBackend: 'opencl',
      },
      baseRuntime,
      limits,
    );

    expect(routed.routeEvaluation.workItem.kind).toBe('llm_step');
    expect(mapBackend(routed.routeEvaluation)).toBe('opencl');
    expect(routed.backend).toBe('opencl');
    expect(routed.modelDecision).toEqual({
      model: 'qwen-7b',
      reason: 'prompt size heuristic',
      overrideApplied: false,
    });
  });

  it('honors AAIS routing hints before prompt heuristics', () => {
    const router = createRouter();
    const routed = routeSovereignXLlmInference(
      router,
      {
        id: 'llm-work-3',
        agentId: 'agent-llm',
        intentId: 'intent-llm',
        prompt: 'short but constitutional',
        promptTokens: 4,
        estimatedFlops: 1_000_000,
        routingHint: {
          preferredModel: 'qwen-7b',
          reason: 'deep reasoning',
        },
      },
      baseRuntime,
      limits,
    );

    expect(routed.modelDecision).toEqual({
      model: 'qwen-7b',
      reason: 'deep reasoning',
      overrideApplied: false,
    });
  });

  it('carries trust metadata through low-trust routed decisions', () => {
    const router = createRouter();
    const trust = {
      score: 0.24,
      band: 'low' as const,
      evidenceIds: ['evidence-1'],
      authority: { stewardId: 'steward-1' },
      provenance: { originSystem: 'relationship-ledger', method: 'assertion' },
    };

    const routed = routeSovereignXLlmInference(
      router,
      {
        id: 'llm-work-5',
        agentId: 'agent-llm',
        intentId: 'intent-llm',
        prompt: 'trust-aware routing request',
        promptTokens: 10,
        estimatedFlops: 1_000_000,
        trust,
      },
      baseRuntime,
      limits,
    );

    expect(routed.modelDecision).toEqual({
      model: 'qwen-3b',
      reason: 'low trust keeps the request on the smaller reasoning surface',
      overrideApplied: false,
      trust,
    });
    expect(routed.routeEvaluation.trust).toEqual(trust);
  });

  it('lets the user override the routed model', () => {
    const router = createRouter();
    router.setOverride('qwen-3b');
    const routed = routeSovereignXLlmInference(
      router,
      {
        id: 'llm-work-4',
        agentId: 'agent-llm',
        intentId: 'intent-llm',
        prompt: 'deep reasoning request that would normally prefer the larger model',
        promptTokens: 72,
        estimatedFlops: 1_000_000,
        routingHint: {
          preferredModel: 'qwen-7b',
          reason: 'deep reasoning',
        },
      },
      baseRuntime,
      limits,
    );

    expect(routed.modelDecision).toEqual({
      model: 'qwen-3b',
      reason: 'user override',
      overrideApplied: true,
    });
  });

  it('invokes the engine directly after routing', async () => {
    const router = createRouter();
    const fetchImpl = async (_input: RequestInfo | URL, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body ?? '{}'));
      return {
        ok: true,
        status: 200,
        json: async () => ({
          backend_used: body.backend,
          completion: 'direct-engine-response',
          fallback: false,
        }),
      } as Response;
    };

    const routed = await invokeSovereignXLlmInference(
      router,
      {
        id: 'llm-work-2',
        agentId: 'agent-llm',
        intentId: 'intent-llm',
        prompt: 'wire the engine',
        promptTokens: 24,
        estimatedFlops: 1_000_000_000,
        maxTokens: 16,
        temperature: 0.1,
        preferredGpuBackend: 'opencl',
      },
      baseRuntime,
      limits,
      {
        engineUrl: 'http://127.0.0.1:8080',
        fetchImpl,
      },
    );

    expect(routed.backend).toBe('opencl');
    expect(routed.engineResponse?.completion).toBe('direct-engine-response');
    expect(routed.engineResponse?.backend_used).toBe('opencl');
  });

  it('requires a signed trust packet and emits a canonical route decision artifact', () => {
    const router = createRouter();
    const trustPacket = createSignedTrustPacket(0.82, 'high', 'full');
    const workItem: WorkItem = {
      id: 'work-artifact',
      agentId: 'agent-artifact',
      kind: 'llm_step',
      intentId: 'intent-llm',
      costEstimateTokens: 64,
      costEstimateFlops: 5_000_000_000,
      costEstimateMs: 50,
      priority: 2,
    };
    const routeEvaluation = router.evaluate(workItem, baseRuntime, limits);

    const routeDecisionArtifact = buildRouteDecisionArtifact({
      requestId: 'request-artifact',
      orgId: 'org-1',
      customerId: 'customer-1',
      relationshipId: trustPacket.relationshipId,
      trustPacket,
      trustPolicy: {
        governanceLevel: 'full',
        minTrustScore: 0.75,
        minTrustBand: 'high',
        preferHighTrustBand: true,
      },
      routeEvaluation,
      provenance: {
        originSystem: 'router-test',
        method: 'unit-test',
        standardsTraceabilityIds: ['stm-router-route-decision'],
      },
      decidedBy: 'governance-kernel',
      signer: 'unit-test',
      signingSecret: 'unit-test-route-secret',
    });

    expect(routeDecisionArtifact.governance.result).toBe('allowed');
    expect(routeDecisionArtifact.trustPacket.signature?.value).toBeTruthy();
    expect(routeDecisionArtifact.signature?.value).toBeTruthy();
  });

  it('marks near-threshold trust as warning and low trust as blocked', () => {
    const router = createRouter();
    const warningPacket = createSignedTrustPacket(0.72, 'medium', 'full');
    const blockedPacket = createSignedTrustPacket(0.14, 'low', 'full');
    const workItem: WorkItem = {
      id: 'work-threshold',
      agentId: 'agent-threshold',
      kind: 'llm_step',
      intentId: 'intent-llm',
      costEstimateTokens: 32,
      costEstimateFlops: 2_000_000_000,
      costEstimateMs: 40,
      priority: 1,
    };
    const routeEvaluation = router.evaluate(workItem, baseRuntime, limits);

    const warningArtifact = buildRouteDecisionArtifact({
      requestId: 'request-warning',
      orgId: 'org-1',
      relationshipId: warningPacket.relationshipId,
      trustPacket: warningPacket,
      trustPolicy: {
        governanceLevel: 'full',
        minTrustScore: 0.75,
        minTrustBand: 'high',
        preferHighTrustBand: true,
      },
      routeEvaluation,
      provenance: {
        originSystem: 'router-test',
        method: 'unit-test',
      },
    });
    const blockedArtifact = buildRouteDecisionArtifact({
      requestId: 'request-blocked',
      orgId: 'org-1',
      relationshipId: blockedPacket.relationshipId,
      trustPacket: blockedPacket,
      trustPolicy: {
        governanceLevel: 'full',
        minTrustScore: 0.75,
        minTrustBand: 'high',
        preferHighTrustBand: true,
      },
      routeEvaluation,
      provenance: {
        originSystem: 'router-test',
        method: 'unit-test',
      },
    });

    expect(warningArtifact.governance.result).toBe('warning');
    expect(blockedArtifact.governance.result).toBe('blocked');
  });
});

describe('SovereignX trust policy helpers', () => {
  it('parses trust clauses in the routing DSL', () => {
    const parsed = parseRoutingDsl(`
      require trust.band != low
      prefer trust.score >= 0.7 [weight=0.6 tier=trust]
    `);

    expect(parsed.clauses).toHaveLength(2);
    expect(parsed.clauses[0].path).toBe('trust.band');
    expect(parsed.clauses[1].annotations).toEqual({ weight: '0.6', tier: 'trust' });
    expect(compileRoutingDsl(parsed).clauses[1].validatedPath).toBe('trust.score');
  });

  it('attaches trust metadata to candidate models', () => {
    const model: CandidateModel = {
      id: 'model-1',
      name: 'Model 1',
      governanceScore: 0.82,
      costScore: 0.67,
      performanceScore: 0.74,
      trustScore: 0,
      trustBand: 'low',
    };

    const trusted = applyTrustToCandidateModel(model, {
      score: 0.83,
      band: 'high',
      evidenceIds: ['evidence-1'],
      authority: { stewardId: 'steward-1' },
      provenance: { originSystem: 'ledger', method: 'assertion' },
    });

    expect(trusted.trustScore).toBe(0.83);
    expect(trusted.trustBand).toBe('high');
    expect(trusted.relationshipTrust?.evidenceIds).toEqual(['evidence-1']);
  });
});

describe('SovereignX proof surface', () => {
  it('validates the router proof surface', () => {
    const validation = validateSovereignXRouterProofSurface();

    expect(validation.passed).toBe(true);
    expect(validation.issues.every((issue) => issue.severity !== 'error')).toBe(true);
  });
});
