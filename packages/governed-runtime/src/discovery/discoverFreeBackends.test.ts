import { describe, expect, it, vi } from 'vitest';
import { discoverFreeBackends, requireFreeBackends } from './discoverFreeBackends.js';

describe('discoverFreeBackends', () => {
  it('discovers Ollama when /api/tags responds', async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes('/api/tags')) {
        return new Response(JSON.stringify({ models: [{ name: 'qwen2.5-coder:3b' }] }), { status: 200 });
      }
      return new Response(null, { status: 404 });
    });

    const result = await discoverFreeBackends({
      fetch: fetchMock as typeof fetch,
      lmStudioUrl: 'http://127.0.0.1:59999',
      cursorUrl: 'http://127.0.0.1:59998',
      devinUrl: 'http://127.0.0.1:59997',
      localLlmUrl: 'http://127.0.0.1:59996',
    });

    expect(result.backends.some((b) => b.name === 'ollama')).toBe(true);
    expect(result.available.some((a) => a.name === 'ollama')).toBe(true);
  });

  it('discovers LM Studio when /v1/models responds', async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes('/v1/models')) {
        return new Response(JSON.stringify({ data: [{ id: 'phi-3-mini' }] }), { status: 200 });
      }
      return new Response(null, { status: 404 });
    });

    const result = await discoverFreeBackends({
      fetch: fetchMock as typeof fetch,
      ollamaUrl: 'http://127.0.0.1:59999',
      cursorUrl: 'http://127.0.0.1:59998',
      devinUrl: 'http://127.0.0.1:59997',
      localLlmUrl: 'http://127.0.0.1:59996',
      lmStudioUrl: 'http://127.0.0.1:1234',
    });

    expect(result.backends.some((b) => b.name === 'lm-studio')).toBe(true);
  });

  it('registers Cursor SDK backend when a Cursor API key is configured', async () => {
    const fetchMock = vi.fn(async () => new Response(null, { status: 404 }));

    const result = await discoverFreeBackends({
      fetch: fetchMock as typeof fetch,
      ollamaUrl: 'http://127.0.0.1:59999',
      lmStudioUrl: 'http://127.0.0.1:59998',
      cursorUrl: 'http://127.0.0.1:59997',
      devinUrl: 'http://127.0.0.1:59996',
      localLlmUrl: 'http://127.0.0.1:59995',
      cursorApiKey: 'cursor-test-key',
      cursorCwd: 'E:/project-infi',
      cursorModel: 'composer-2.5',
    });

    expect(result.backends.some((b) => b.name === 'cursor' && b.supports.tools)).toBe(true);
    expect(result.available).toContainEqual({
      name: 'cursor',
      url: 'cursor-sdk:E:/project-infi',
      models: ['composer-2.5'],
    });
  });

  it('uses manual backends when supplied', async () => {
    const result = await discoverFreeBackends({
      backends: [{ name: 'custom', supports: { chat: true, code: true }, chat: async () => ({}) as never }],
    });

    expect(result.backends).toHaveLength(1);
    expect(result.backends[0]?.name).toBe('custom');
  });

  it('requireFreeBackends throws when empty', () => {
    expect(() => requireFreeBackends({ backends: [], available: [], skipped: [] })).toThrow(
      /No free local agents found/,
    );
  });
});