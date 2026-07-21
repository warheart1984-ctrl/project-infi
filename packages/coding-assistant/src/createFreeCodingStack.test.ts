import { describe, expect, it, vi } from 'vitest';
import { createFreeCodingStack } from './createFreeCodingStack.js';

describe('createFreeCodingStack', () => {
  it('wires assistant with discovered backends', async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes('/api/tags')) {
        return new Response(JSON.stringify({ models: [{ name: 'qwen2.5-coder:3b' }] }), { status: 200 });
      }
      return new Response(null, { status: 404 });
    });

    const stack = await createFreeCodingStack({
      fetch: fetchMock as typeof fetch,
      lmStudioUrl: 'http://127.0.0.1:59999',
      cursorUrl: 'http://127.0.0.1:59998',
      devinUrl: 'http://127.0.0.1:59997',
      localLlmUrl: 'http://127.0.0.1:59996',
    });

    expect(stack.backends.length).toBeGreaterThan(0);
    expect(stack.assistant.getRouter()).toBe(stack.router);
    expect(stack.assistant.getAAISRuntime()).toBe(stack.aais);
    expect(stack.assistant.getSovereignXRouter()).toBe(stack.sovereignXRouter);
    expect(stack.discovery.available.some((a) => a.name === 'ollama')).toBe(true);
  });
});
