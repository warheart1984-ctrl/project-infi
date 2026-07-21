import { PatternLedger } from '@aaes-os/aaes-governance';
import { AAISRuntime } from '@aaes-os/aais';
import {
  CodingRouter,
  discoverFreeBackends,
  loadCodingPolicyPack,
  loadFreeCodingPolicyPack,
  OllamaBackend,
  requireFreeBackends,
  type CodingBackend,
  type DiscoveryOptions,
  type DiscoveryResult,
} from '@aaes-os/governed-runtime';
import { SovereignXRouter } from '@aaes-os/sovereignx-router';
import { CodingAssistant } from './CodingAssistant.js';
import { SovereignXOllamaBackend } from './SovereignXOllamaBackend.js';

export interface FreeCodingStackOptions extends DiscoveryOptions {
  /** Extra backends appended after auto-discovery. */
  additionalBackends?: CodingBackend[];
  /** Use free-only policy pack (default: true). Set false to use cloud policy pack. */
  freePolicies?: boolean;
}

export interface FreeCodingStack {
  assistant: CodingAssistant;
  aais: AAISRuntime;
  sovereignXRouter?: SovereignXRouter;
  router: CodingRouter;
  discovery: DiscoveryResult;
  backends: CodingBackend[];
}

function hasModels(models: string[] | undefined, required: readonly string[]): boolean {
  if (!models) {
    return false;
  }
  const normalized = new Set(models.map((model) => model.toLowerCase()));
  return required.every((model) => normalized.has(model.toLowerCase()));
}

/**
 * Zero-cost setup: auto-discovers Ollama, LM Studio, Cursor, Devin, and local LLMs.
 * No API keys required.
 */
export async function createFreeCodingStack(
  options: FreeCodingStackOptions = {},
): Promise<FreeCodingStack> {
  const discovery = await discoverFreeBackends(options);
  const discoveredBackends = requireFreeBackends(discovery);
  const backends = [...discoveredBackends];
  const sovereignXRouter = new SovereignXRouter();
  const aais = new AAISRuntime();

  const policies =
    options.freePolicies === false ? loadCodingPolicyPack() : loadFreeCodingPolicyPack();

  const ollamaAvailable = discovery.available.find((agent) => agent.name === 'ollama');
  if (ollamaAvailable && hasModels(ollamaAvailable.models, ['qwen2.5-coder:3b', 'qwen2.5-coder:7b'])) {
    const fetchImpl = options.fetch ?? globalThis.fetch;
    const ollamaUrl = ollamaAvailable.url.replace(/\/$/, '');
    const shortBackend = new OllamaBackend({
      baseUrl: ollamaUrl,
      model: 'qwen2.5-coder:3b',
      name: 'qwen2.5-coder:3b',
      fetch: fetchImpl,
    });
    const longBackend = new OllamaBackend({
      baseUrl: ollamaUrl,
      model: 'qwen2.5-coder:7b',
      name: 'qwen2.5-coder:7b',
      fetch: fetchImpl,
    });

    const sovereignXBackend = new SovereignXOllamaBackend({
      name: 'ollama',
      shortBackend,
      longBackend,
      router: sovereignXRouter,
      aaisRuntime: aais,
    });
    backends.splice(
      0,
      backends.length,
      sovereignXBackend,
      ...backends.filter((backend) => backend.name !== 'ollama'),
      ...(options.additionalBackends ?? []),
    );
  } else {
    backends.push(...(options.additionalBackends ?? []));
  }

  const ledger = new PatternLedger();
  const router = new CodingRouter(backends, policies, ledger);
  const assistant = new CodingAssistant(router, aais, sovereignXRouter);

  return { assistant, aais, sovereignXRouter, router, discovery, backends };
}

/** Alias for createFreeCodingStack — use any free local agent with one call. */
export const createFreeCodingAssistant = createFreeCodingStack;
