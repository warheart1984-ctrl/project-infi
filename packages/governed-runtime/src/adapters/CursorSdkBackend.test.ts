import { describe, expect, it, vi } from 'vitest';
import { CursorSdkBackend } from './CursorSdkBackend.js';
import type { GovernedChatRequest } from '../types.js';

function makeRequest(): GovernedChatRequest {
  return {
    intent: { id: 'intent-1', kind: 'refactor', description: 'Refactor local project' },
    identity: { actorId: 'dev-1', role: 'developer' },
    governance: { domain: 'coding', risk: 'high', tags: ['local-project'] },
    trace: {
      traceId: 'trace-1',
      intentId: 'intent-1',
      actorId: 'dev-1',
      policyIds: [],
      timestamps: { createdAt: 1 },
    },
    input: {
      systemPrompt: 'Follow governed runtime rules.',
      userContent: 'Update the adapter.',
    },
  };
}

describe('CursorSdkBackend', () => {
  it('runs Cursor Agent.prompt with explicit local runtime and governed prompt text', async () => {
    const prompt = vi.fn(async () => ({
      status: 'finished' as const,
      id: 'run-1',
      result: 'patch ready',
      durationMs: 42,
      usage: {
        inputTokens: 11,
        outputTokens: 7,
        cacheReadTokens: 0,
        cacheWriteTokens: 0,
        totalTokens: 18,
      },
    }));

    const backend = new CursorSdkBackend({
      apiKey: 'cursor-test-key',
      cwd: 'E:/project-infi',
      cursorModule: {
        Agent: { prompt },
        CursorAgentError: class CursorAgentError extends Error {},
      },
    });

    const response = await backend.chat(makeRequest());

    expect(prompt).toHaveBeenCalledWith('Follow governed runtime rules.\n\nUpdate the adapter.', {
      apiKey: 'cursor-test-key',
      model: { id: 'composer-2.5' },
      local: { cwd: 'E:/project-infi' },
    });
    expect(response.backendName).toBe('cursor');
    expect(response.output.text).toBe('patch ready');
    expect(response.output.tokensIn).toBe(11);
    expect(response.output.tokensOut).toBe(7);
    expect(response.output.latencyMs).toBe(42);
  });

  it('fails closed when Cursor returns a non-finished run result', async () => {
    const backend = new CursorSdkBackend({
      apiKey: 'cursor-test-key',
      cwd: 'E:/project-infi',
      cursorModule: {
        Agent: {
          prompt: vi.fn(async () => ({ status: 'cancelled' as const, id: 'run-cancelled' })),
        },
      },
    });

    await expect(backend.chat(makeRequest())).rejects.toThrow(
      'Cursor run did not finish (cancelled): run-cancelled',
    );
  });
});