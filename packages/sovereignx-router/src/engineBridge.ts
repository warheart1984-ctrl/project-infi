import type {
  GovernanceLimits,
  RouteEvaluation,
  RuntimeStats,
  RelationshipTrustView,
  SovereignXModelDecision,
  SovereignXRoutingHint,
  WorkItem,
} from './types.js';
import type { GovernanceTrustPolicy, GovernanceTrustLevel } from './trust.js';
import type { SovereignXRouter } from './SovereignXRouter.js';

export type SovereignXEngineBackend = 'cpu' | 'opencl' | 'vulkan';

export interface SovereignXLlmInferenceRequest {
  id: string;
  agentId: string;
  intentId: string;
  prompt: string;
  promptTokens: number;
  estimatedFlops: number;
  maxTokens?: number;
  temperature?: number;
  model?: string;
  priority?: number;
  tenantId?: string;
  preferredGpuBackend?: Exclude<SovereignXEngineBackend, 'cpu'>;
  routingHint?: SovereignXRoutingHint;
  trust?: RelationshipTrustView;
  governanceLevel?: GovernanceTrustLevel;
  trustPolicy?: GovernanceTrustPolicy;
}

export interface SovereignXLlmRoutingResult {
  routeEvaluation: RouteEvaluation;
  backend: SovereignXEngineBackend | 'delay' | 'drop';
  modelDecision: SovereignXModelDecision;
}

export interface SovereignXEngineRuntimeOptions {
  engineUrl: string;
  fetchImpl?: typeof fetch;
}

export interface SovereignXEngineResponse {
  backend_used: string;
  completion: string;
  error?: string;
  latency_ms?: number;
  tokens_generated?: number;
  tokens_per_second?: number;
  fallback?: boolean;
}

export function routeSovereignXLlmInference(
  router: SovereignXRouter,
  request: SovereignXLlmInferenceRequest,
  runtime: RuntimeStats,
  limits: GovernanceLimits,
): SovereignXLlmRoutingResult {
  const workItem: WorkItem = {
    id: request.id,
    agentId: request.agentId,
    kind: 'llm_step',
    intentId: request.intentId,
    costEstimateTokens: request.promptTokens,
    costEstimateFlops: request.estimatedFlops,
    priority: request.priority,
    tenantId: request.tenantId,
  };

  const routeEvaluation = router.evaluate(workItem, runtime, limits);
  const trust = request.trust
    ? {
        score: request.trust.score,
        band: request.trust.band,
        evidenceIds: [...request.trust.evidenceIds],
        authority: request.trust.authority ? { ...request.trust.authority } : undefined,
        provenance: request.trust.provenance ? { ...request.trust.provenance } : undefined,
      }
    : undefined;
  const modelDecision = router.resolveModelDecision({
    promptTokens: request.promptTokens,
    routingHint: request.routingHint,
    trust,
    governanceLevel: request.governanceLevel,
    trustPolicy: request.trustPolicy,
  });
  const routedRouteEvaluation = trust ? { ...routeEvaluation, trust, modelDecision: { ...modelDecision, trust } } : routeEvaluation;
  return {
    routeEvaluation: routedRouteEvaluation,
    backend: mapBackend(routeEvaluation, request.preferredGpuBackend),
    modelDecision: trust ? { ...modelDecision, trust } : modelDecision,
  };
}

export function mapBackend(
  routeEvaluation: RouteEvaluation,
  preferredGpuBackend: Exclude<SovereignXEngineBackend, 'cpu'> = 'opencl',
): SovereignXEngineBackend | 'delay' | 'drop' {
  const target = routeEvaluation.effectiveDecision.target;
  if (target === 'DELAY') {
    return 'delay';
  }
  if (target === 'DROP') {
    return 'drop';
  }
  if (target === 'GPU') {
    return preferredGpuBackend;
  }
  return 'cpu';
}

export async function invokeSovereignXLlmInference(
  router: SovereignXRouter,
  request: SovereignXLlmInferenceRequest,
  runtime: RuntimeStats,
  limits: GovernanceLimits,
  options: SovereignXEngineRuntimeOptions,
): Promise<{
  routeEvaluation: RouteEvaluation;
  backend: SovereignXEngineBackend | 'delay' | 'drop';
  modelDecision: SovereignXModelDecision;
  engineResponse?: SovereignXEngineResponse;
}> {
  const routed = routeSovereignXLlmInference(router, request, runtime, limits);
  if (routed.backend === 'delay' || routed.backend === 'drop') {
    return routed;
  }

  const fetchImpl = options.fetchImpl ?? fetch;
  const response = await fetchImpl(`${options.engineUrl.replace(/\/+$/, '')}/v1/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: request.model ?? 'llm-engine-local',
      backend: routed.backend,
      temperature: request.temperature ?? 0.2,
      max_tokens: request.maxTokens ?? 256,
      messages: [
        {
          role: 'user',
          content: request.prompt,
        },
      ],
    }),
  });

  if (!response.ok) {
    throw new Error(`SovereignX engine request failed with HTTP ${response.status}`);
  }

  const payload = (await response.json()) as SovereignXEngineResponse;
  return {
    ...routed,
    engineResponse: payload,
  };
}
