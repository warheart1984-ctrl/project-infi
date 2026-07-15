import {
  routeSovereignXLlmInference,
  type GovernanceLimits,
  type RouteEvaluation,
  type RuntimeStats,
  type SovereignXEngineBackend,
  type SovereignXLlmRoutingResult,
  type SovereignXModelDecision,
  type SovereignXRouter,
  type SovereignXRoutingHint,
} from '@aaes-os/sovereignx-router';

import type { RequestPacket } from './codex-handoff-core.js';

export interface CodexHandoffRouteContext {
  request: RequestPacket;
  replyPath?: string;
  hasReply: boolean;
}

export interface CodexHandoffRouteResult {
  requestId: string;
  promptTokens: number;
  selectedModel: SovereignXModelDecision['model'];
  routeEvaluation: RouteEvaluation;
  backend: SovereignXEngineBackend | 'delay' | 'drop';
  modelDecision: SovereignXModelDecision;
  reason: string;
}

const DEFAULT_RUNTIME: RuntimeStats = {
  activeGpuJobs: 0,
  activeCpuJobs: 0,
  gpuUtil: 0,
  cpuUtil: 0,
  gpuTempC: 44,
  vramUsedBytes: 0,
  vramTotalBytes: 24 * 1024 * 1024 * 1024,
};

const DEFAULT_LIMITS: GovernanceLimits = {
  maxGpuJobs: 2,
  maxCpuJobs: 32,
  maxConcurrentJobs: 8,
  maxGpuTempC: 82,
  maxVramBytes: 20 * 1024 * 1024 * 1024,
  maxTokensPerAgentPerMin: 8_000,
  maxFlopsPerAgentPerMin: 50_000_000,
};

function stableHash(input: string): string {
  let hash = 2166136261;
  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `codex-${(hash >>> 0).toString(16).padStart(8, '0')}`;
}

function joinDefined(values: Array<string | undefined>): string[] {
  return values.filter((value): value is string => typeof value === 'string' && value.trim().length > 0);
}

function estimatePromptTokens(request: RequestPacket, hasReply: boolean): number {
  const characters = joinDefined([
    request.objective,
    request.current_state,
    request.next_action,
    request.verification,
    ...request.done,
    ...request.files,
    ...request.blockers,
  ])
    .join(' ').length;

  const structuralTokens = request.done.length + request.files.length + request.blockers.length + 3;
  const replyPenalty = hasReply ? 4 : 0;
  return Math.max(1, Math.ceil(characters / 12) + structuralTokens + replyPenalty);
}

function buildPrompt(request: RequestPacket, hasReply: boolean): string {
  return [
    `objective: ${request.objective}`,
    request.current_state ? `current_state: ${request.current_state}` : null,
    `done: ${request.done.join(' | ') || '(none)'}`,
    `files: ${request.files.join(' | ') || '(none)'}`,
    `next_action: ${request.next_action}`,
    `verification: ${request.verification}`,
    `blockers: ${request.blockers.join(' | ') || '(none)'}`,
    `reply_present: ${hasReply ? 'yes' : 'no'}`,
  ]
    .filter((line): line is string => typeof line === 'string')
    .join('\n');
}

export function createCodexHandoffRouter(router: SovereignXRouter): SovereignXRouter {
  router.registerIntent({
    id: 'codex-handoff',
    domain: 'governance',
    rules: 'Route handoff packets through constitutional orchestration before any reasoning engine is selected.',
    allowedTargets: ['CPU', 'GPU', 'DELAY', 'DROP'],
    maxTokensPerAgentPerMin: DEFAULT_LIMITS.maxTokensPerAgentPerMin,
    maxFlopsPerAgentPerMin: DEFAULT_LIMITS.maxFlopsPerAgentPerMin,
  });
  return router;
}

export function createDefaultCodexHandoffRouter(clock?: () => number): SovereignXRouter {
  return createCodexHandoffRouter(new SovereignXRouter(clock ? { clock } : {}));
}

export function routeCodexHandoff(
  router: SovereignXRouter,
  context: CodexHandoffRouteContext,
): CodexHandoffRouteResult {
  const promptTokens = estimatePromptTokens(context.request, context.hasReply);
  const requestId = stableHash(
    [
      context.request.objective,
      context.request.current_state ?? '',
      context.request.next_action,
      context.request.verification,
      context.replyPath ?? '',
      context.hasReply ? 'reply' : 'request',
    ].join('|'),
  );

  const routed: SovereignXLlmRoutingResult = routeSovereignXLlmInference(
    router,
    {
      id: requestId,
      agentId: 'codex-handoff',
      intentId: 'codex-handoff',
      prompt: buildPrompt(context.request, context.hasReply),
      promptTokens,
      estimatedFlops: promptTokens * 1_200,
      maxTokens: 768,
      temperature: 0.2,
      model: promptTokens > 18 ? 'qwen-7b' : 'qwen-3b',
      priority: context.hasReply ? 2 : 1,
      routingHint: {
        preferredModel: promptTokens > 18 ? 'qwen-7b' : 'qwen-3b',
        reason: context.hasReply ? 'reply ingestion requires a fuller reasoning surface' : 'request packet is kept deliberately minimal',
      } satisfies SovereignXRoutingHint,
    },
    DEFAULT_RUNTIME,
    DEFAULT_LIMITS,
  );

  return {
    requestId,
    promptTokens,
    selectedModel: routed.modelDecision.model,
    routeEvaluation: routed.routeEvaluation,
    backend: routed.backend,
    modelDecision: routed.modelDecision,
    reason: routed.modelDecision.reason,
  };
}
