import { SovereignXRouter, routeSovereignXLlmInference } from '@aaes-os/sovereignx-router';
import type { AAISExecutionReport, AAISRuntime } from '@aaes-os/aais';
import { recordRoutingEvent, resolveRoutingHint } from '@aaes-os/aais';
import type { CodingBackend, GovernedChatRequest } from '@aaes-os/governed-runtime';

type RoutedBackend = Pick<CodingBackend, 'chat' | 'supports' | 'name'>;

export interface SovereignXOllamaBackendOptions {
  shortBackend: RoutedBackend;
  longBackend: RoutedBackend;
  router?: SovereignXRouter;
  aaisRuntime?: Pick<AAISRuntime, 'executeAAISCheck'>;
  shortPromptTokenThreshold?: number;
  name?: string;
}

function estimatePromptTokens(req: GovernedChatRequest): number {
  const content = `${req.input.systemPrompt}\n${req.input.userContent}`.trim();
  if (!content) {
    return 1;
  }
  return Math.max(1, content.split(/\s+/).filter(Boolean).length);
}

export class SovereignXOllamaBackend implements CodingBackend {
  readonly name: string;
  readonly supports = { chat: true, code: true };

  private readonly router: SovereignXRouter;
  private readonly shortBackend: RoutedBackend;
  private readonly longBackend: RoutedBackend;
  private readonly aaisRuntime?: Pick<AAISRuntime, 'executeAAISCheck'>;
  private readonly threshold: number;

  constructor(options: SovereignXOllamaBackendOptions) {
    this.name = options.name ?? 'ollama';
    this.router = options.router ?? new SovereignXRouter();
    this.shortBackend = options.shortBackend;
    this.longBackend = options.longBackend;
    this.aaisRuntime = options.aaisRuntime;
    this.threshold = options.shortPromptTokenThreshold ?? 18;
  }

  async chat(req: GovernedChatRequest) {
    const promptTokens = estimatePromptTokens(req);
    const aaisReport = this.runAAIS(req);
    this.router.registerIntent({
      id: req.trace.intentId,
      domain: 'llm_step',
      rules: 'SovereignX routes Ollama coding requests across the local model pair.',
      allowedTargets: ['CPU', 'GPU'],
      maxTokensPerAgentPerMin: 100_000,
      maxFlopsPerAgentPerMin: 1_000_000_000_000,
    });
    const route = routeSovereignXLlmInference(
      this.router,
      {
        id: req.trace.traceId,
        agentId: req.identity.actorId,
        intentId: req.intent.id,
        prompt: req.input.userContent,
        promptTokens,
        estimatedFlops: promptTokens * 4_000,
        maxTokens: req.trace.policyIds.length > 0 ? 512 : 256,
        temperature: 0.2,
        routingHint: aaisReport.routingHint,
      },
      {
        activeGpuJobs: 0,
        activeCpuJobs: 0,
        gpuUtil: 25,
        cpuUtil: 25,
        gpuTempC: 52,
        vramUsedBytes: 0,
        vramTotalBytes: 24 * 1024 * 1024 * 1024,
      },
      {
        maxGpuJobs: promptTokens > this.threshold ? 1 : 0,
        maxCpuJobs: 8,
        maxConcurrentJobs: 8,
        maxGpuTempC: 85,
        maxVramBytes: 24 * 1024 * 1024 * 1024,
        maxTokensPerAgentPerMin: 100_000,
        maxFlopsPerAgentPerMin: 100_000_000,
      },
    );

    if (route.backend === 'drop') {
      throw new Error('SovereignX routed this request to DROP');
    }
    if (route.backend === 'delay') {
      return this.shortBackend.chat(req);
    }

    const backend = route.modelDecision.model === 'qwen-3b' ? this.shortBackend : this.longBackend;
    if (aaisReport.provenance) {
      aaisReport.provenance.routerDecision = {
        model: route.modelDecision.model,
        reason: route.modelDecision.reason,
        overrideApplied: route.modelDecision.overrideApplied,
      };
    }
    recordRoutingEvent({
      capabilityName: aaisReport.provenance?.capabilityName ?? 'Capability Discovery Engine',
      model: route.modelDecision.model,
      overrideApplied: route.modelDecision.overrideApplied,
      hintUsed: Boolean(aaisReport.routingHint?.preferredModel),
      heuristicFallback: route.modelDecision.reason === 'prompt size heuristic' && !aaisReport.routingHint?.preferredModel,
    });
    return backend.chat(req);
  }

  private runAAIS(req: GovernedChatRequest): AAISExecutionReport {
    if (!this.aaisRuntime) {
      const payload = {
        systemPrompt: req.input.systemPrompt,
        userContent: req.input.userContent,
        context: req.input.context,
      };
      const routingHint = resolveRoutingHint(payload);
      return {
        flow: ['llm', 'jarvis', 'nova'],
        stages: [
          { stage: 'llm', passed: true },
          { stage: 'jarvis', passed: true },
          { stage: 'nova', passed: true },
        ],
        payload: {
          systemPrompt: req.input.systemPrompt,
          userContent: req.input.userContent,
          context: req.input.context,
        },
        validation: { passed: true },
        message: null,
        routingHint,
        provenance: {
          capabilityName: 'Capability Discovery Engine',
          capabilityFile: 'packages/aais/src/capabilities.ts',
          resolver: 'SovereignXOllamaBackend.runAAIS',
          routingHint,
        },
      };
    }

    return this.aaisRuntime.executeAAISCheck({
      surface: 'llm',
      flow: ['llm', 'jarvis', 'nova'],
      capabilities: ['Capability Discovery Engine', 'Reference Runtime Composer'],
      payload: {
        systemPrompt: req.input.systemPrompt,
        userContent: req.input.userContent,
        context: req.input.context,
      },
    });
  }
}
