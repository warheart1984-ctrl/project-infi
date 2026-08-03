import type { GovernanceLimits, RouteEvaluation, RuntimeStats, WorkItem } from './types.js';
import type { SovereignXRouter } from './SovereignXRouter.js';

export type SovereignXRenderBackend =
  | 'canvas'
  | 'webgpu'
  | 'vulkan'
  | 'opencl'
  | 'unreal'
  | 'unity'
  | 'remote-gpu';

export interface SovereignXRenderAdapter {
  id: string;
  backend: SovereignXRenderBackend;
  available: boolean;
  deviceClass: 'cpu' | 'integrated-gpu' | 'discrete-gpu' | 'remote-gpu';
  name?: string;
  vramBytes?: number;
  features?: string[];
  powerPreference?: 'low-power' | 'high-performance';
  nodeId?: string;
  /** Local-only opaque adapter handle; never include in serialized evidence. */
  runtimeHandle?: unknown;
}

export interface SovereignXRenderRequest {
  id: string;
  agentId: string;
  intentId: string;
  sceneId: string;
  width: number;
  height: number;
  frames: number;
  estimatedFlops: number;
  estimatedMs?: number;
  priority?: number;
  preferredBackends?: SovereignXRenderBackend[];
  requiredFeatures?: string[];
  minimumVramBytes?: number;
  allowCpuFallback?: boolean;
}

export interface SovereignXRenderRouteResult {
  action: 'dispatch' | 'delay' | 'drop';
  backend: SovereignXRenderBackend | 'delay' | 'drop';
  adapter: SovereignXRenderAdapter | null;
  routeEvaluation: RouteEvaluation;
  reason: string;
  evidenceRefs: string[];
}

export function registerSovereignXRenderIntent(
  router: SovereignXRouter,
  intentId = 'intent-4d-render',
): void {
  router.registerIntent({
    id: intentId,
    domain: 'render_frame',
    rules: '4D render work may use governed GPU execution with a CPU Canvas fallback',
    allowedTargets: ['GPU', 'CPU'],
  });
}

export function routeSovereignXRender(
  router: SovereignXRouter,
  request: SovereignXRenderRequest,
  runtime: RuntimeStats,
  limits: GovernanceLimits,
  adapters: SovereignXRenderAdapter[],
): SovereignXRenderRouteResult {
  const workItem: WorkItem = {
    id: request.id,
    agentId: request.agentId,
    kind: 'render_frame',
    intentId: request.intentId,
    costEstimateTokens: 0,
    costEstimateFlops: request.estimatedFlops,
    costEstimateMs: request.estimatedMs,
    priority: request.priority,
  };
  const routeEvaluation = router.evaluate(workItem, runtime, limits);
  const target = routeEvaluation.effectiveDecision.target;
  const evidenceRefs = [routeEvaluation.evidence.id];

  if (target === 'DROP') return { action: 'drop', backend: 'drop', adapter: null, routeEvaluation, reason: routeEvaluation.effectiveDecision.reason, evidenceRefs };
  if (target === 'DELAY') return { action: 'delay', backend: 'delay', adapter: null, routeEvaluation, reason: routeEvaluation.effectiveDecision.reason, evidenceRefs };

  const eligible = adapters.filter((adapter) => adapter.available &&
    (adapter.vramBytes === undefined || adapter.vramBytes >= (request.minimumVramBytes ?? 0)) &&
    (request.requiredFeatures ?? []).every((feature) => adapter.features?.includes(feature)));

  const selected = target === 'GPU'
    ? selectGpuAdapter(eligible, request.preferredBackends)
    : eligible.find((adapter) => adapter.backend === 'canvas');

  if (selected) {
    return { action: 'dispatch', backend: selected.backend, adapter: { ...selected }, routeEvaluation, reason: `${routeEvaluation.effectiveDecision.reason}; selected ${selected.id}`, evidenceRefs };
  }

  const canvas = request.allowCpuFallback === false ? undefined : eligible.find((adapter) => adapter.backend === 'canvas');
  if (canvas) {
    return { action: 'dispatch', backend: 'canvas', adapter: { ...canvas }, routeEvaluation, reason: `${routeEvaluation.effectiveDecision.reason}; compatible GPU unavailable, using Canvas`, evidenceRefs };
  }

  return { action: 'delay', backend: 'delay', adapter: null, routeEvaluation, reason: 'no eligible render adapter is available', evidenceRefs };
}

function selectGpuAdapter(adapters: SovereignXRenderAdapter[], preferred: SovereignXRenderBackend[] = []): SovereignXRenderAdapter | undefined {
  const gpu = adapters.filter((adapter) => adapter.deviceClass !== 'cpu' && adapter.backend !== 'canvas');
  const backendRank = (backend: SovereignXRenderBackend): number => {
    const explicit = preferred.indexOf(backend);
    if (explicit >= 0) return 1_000 - explicit;
    return ({ webgpu: 80, vulkan: 70, opencl: 60, 'remote-gpu': 50, unreal: 40, unity: 30, canvas: 0 } as const)[backend];
  };
  return gpu.sort((a, b) =>
    backendRank(b.backend) - backendRank(a.backend) ||
    Number(b.deviceClass === 'discrete-gpu') - Number(a.deviceClass === 'discrete-gpu') ||
    (b.vramBytes ?? 0) - (a.vramBytes ?? 0) ||
    a.id.localeCompare(b.id),
  )[0];
}
