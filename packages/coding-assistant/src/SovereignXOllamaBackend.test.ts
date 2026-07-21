import { describe, expect, it, vi } from 'vitest';

import type { CodingBackend, GovernedChatRequest } from '@aaes-os/governed-runtime';

import { SovereignXOllamaBackend } from './SovereignXOllamaBackend.js';

function createRequest(userContent: string): GovernedChatRequest {
  return {
    intent: {
      id: 'intent-1',
      kind: 'coding',
      description: 'test',
    },
    identity: {
      actorId: 'jon',
      role: 'developer',
    },
    governance: {
      domain: 'coding',
      risk: 'low',
      tags: ['general'],
    },
    trace: {
      traceId: 'trace-1',
      intentId: 'intent-1',
      actorId: 'jon',
      policyIds: [],
      timestamps: { createdAt: 1_700_000_000_000 },
    },
    input: {
      systemPrompt: 'You are Nova.',
      userContent,
      context: '',
    },
  };
}

function createBackend(name: string): CodingBackend {
  return {
    name,
    supports: { chat: true, code: true },
    chat: vi.fn(async (req: GovernedChatRequest) => ({
      intentId: req.intent.id,
      backendName: name,
      trace: req.trace,
      output: {
        text: `${name}:${req.input.userContent}`,
        tokensIn: 1,
        tokensOut: 1,
        latencyMs: 0,
      },
      governance: {
        policyIds: [],
        violations: [],
      },
    })),
  };
}

describe('SovereignXOllamaBackend', () => {
  it('routes short prompts to qwen2.5-coder:3b and long prompts to qwen2.5-coder:7b', async () => {
    const shortBackend = createBackend('qwen2.5-coder:3b');
    const longBackend = createBackend('qwen2.5-coder:7b');
    const router = new SovereignXOllamaBackend({
      shortBackend,
      longBackend,
    });

    const shortResult = await router.chat(createRequest('Fix this bug'));
    const longResult = await router.chat(
      createRequest(
        'Analyze this long multi-file refactor request with detailed architectural constraints and compare multiple implementation paths before choosing the safest one.',
      ),
    );

    expect(shortBackend.chat).toHaveBeenCalledTimes(1);
    expect(longBackend.chat).toHaveBeenCalledTimes(1);
    expect(shortResult.backendName).toBe('qwen2.5-coder:3b');
    expect(longResult.backendName).toBe('qwen2.5-coder:7b');
  });

  it('honors AAIS routing hints before the local prompt-size fallback', async () => {
    const shortBackend = createBackend('qwen2.5-coder:3b');
    const longBackend = createBackend('qwen2.5-coder:7b');
    const router = new SovereignXOllamaBackend({
      shortBackend,
      longBackend,
      aaisRuntime: {
        executeAAISCheck: vi.fn(() => ({
          flow: ['llm', 'jarvis', 'nova'],
          stages: [
            { stage: 'llm', passed: true },
            { stage: 'jarvis', passed: true },
            { stage: 'nova', passed: true },
          ],
          payload: {},
          validation: { passed: true },
          message: null,
          routingHint: {
            preferredModel: 'qwen-7b',
            reason: 'deep reasoning',
          },
        })),
      },
    });

    const result = await router.chat(createRequest('Fix this bug'));

    expect(longBackend.chat).toHaveBeenCalledTimes(1);
    expect(shortBackend.chat).not.toHaveBeenCalled();
    expect(result.backendName).toBe('qwen2.5-coder:7b');
  });
});
