import { afterEach, describe, expect, it, vi } from 'vitest';

import { PollinationsProvider } from './pollinations.js';

const PNG_BYTES = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00]);

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

function imageResponse(bytes: Buffer, status = 200): Response {
  return new Response(new Blob([new Uint8Array(bytes)]), {
    status,
    headers: { 'content-type': 'image/png' },
  });
}

describe('PollinationsProvider', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('lists models from the /models endpoint', async () => {
    const fetchImpl = vi.fn(async () => jsonResponse(['sana', 'flux']));
    const provider = new PollinationsProvider('https://image.pollinations.ai', fetchImpl as unknown as typeof fetch);
    const models = await provider.listModels();
    expect(models).toEqual(['sana', 'flux']);
    expect(fetchImpl).toHaveBeenCalledWith('https://image.pollinations.ai/models', { signal: undefined });
  });

  it('falls back to known models when the endpoint fails', async () => {
    const fetchImpl = vi.fn(async () => jsonResponse('boom', 500));
    const provider = new PollinationsProvider('https://image.pollinations.ai', fetchImpl as unknown as typeof fetch);
    const models = await provider.listModels();
    expect(models).toEqual(['sana']);
  });

  it('falls back when the endpoint returns non-array data', async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({ models: ['sana'] }));
    const provider = new PollinationsProvider('https://image.pollinations.ai', fetchImpl as unknown as typeof fetch);
    const models = await provider.listModels();
    expect(models).toEqual(['sana']);
  });

  it('builds a url-encoded text-to-image request', async () => {
    const fetchImpl = vi.fn(async () => imageResponse(PNG_BYTES));
    const provider = new PollinationsProvider('https://image.pollinations.ai', fetchImpl as unknown as typeof fetch);
    await provider.generate({ prompt: 'a red fox', width: 512, height: 384, seed: 42 });
    const [url] = fetchImpl.mock.calls[0] as [string];
    expect(url).toContain('https://image.pollinations.ai/prompt/a%20red%20fox?');
    expect(url).toContain('model=sana');
    expect(url).toContain('width=512');
    expect(url).toContain('height=384');
    expect(url).toContain('seed=42');
    expect(url).not.toContain('image=');
  });

  it('appends the reference image as a url for image-to-image', async () => {
    const fetchImpl = vi.fn(async () => imageResponse(PNG_BYTES));
    const provider = new PollinationsProvider('https://image.pollinations.ai', fetchImpl as unknown as typeof fetch);
    await provider.generate({
      prompt: 'watercolor version',
      referenceImage: { kind: 'url', url: 'https://example.com/photo.jpg' },
    });
    const [url] = fetchImpl.mock.calls[0] as [string];
    expect(url).toContain('image=https%3A%2F%2Fexample.com%2Fphoto.jpg');
  });

  it('appends a data uri reference for local image-to-image', async () => {
    const fetchImpl = vi.fn(async () => imageResponse(PNG_BYTES));
    const provider = new PollinationsProvider('https://image.pollinations.ai', fetchImpl as unknown as typeof fetch);
    const dataUrl = 'data:image/png;base64,aGVsbG8=';
    await provider.generate({
      prompt: 'neon version',
      referenceImage: { kind: 'dataUrl', dataUrl },
    });
    const [url] = fetchImpl.mock.calls[0] as [string];
    expect(url).toContain(encodeURIComponent(dataUrl));
  });

  it('returns bytes with a detected content type', async () => {
    const fetchImpl = vi.fn(async () => imageResponse(PNG_BYTES));
    const provider = new PollinationsProvider('https://image.pollinations.ai', fetchImpl as unknown as typeof fetch);
    const result = await provider.generate({ prompt: 'cat' });
    expect(result.provider).toBe('pollinations');
    expect(result.model).toBe('sana');
    expect(result.contentType).toBe('image/png');
    expect(Buffer.isBuffer(result.bytes)).toBe(true);
  });

  it('throws with the API message on non-2xx responses', async () => {
    const fetchImpl = vi.fn(async () =>
      jsonResponse({ message: 'kontext model is only available on enter.pollinations.ai' }, 500),
    );
    const provider = new PollinationsProvider('https://image.pollinations.ai', fetchImpl as unknown as typeof fetch);
    await expect(provider.generate({ prompt: 'cat' })).rejects.toThrow(
      /kontext model is only available/,
    );
  });

  it('throws on empty prompts', async () => {
    const provider = new PollinationsProvider(undefined, (() => ({})) as unknown as typeof fetch);
    await expect(provider.generate({ prompt: '   ' })).rejects.toThrow(/non-empty prompt/);
  });

  it('forwards an abort signal', async () => {
    const signal = new AbortController().signal;
    const fetchImpl = vi.fn(async () => imageResponse(PNG_BYTES));
    const provider = new PollinationsProvider('https://image.pollinations.ai', fetchImpl as unknown as typeof fetch);
    await provider.generate({ prompt: 'cat' }, { signal });
    expect(fetchImpl).toHaveBeenCalledWith(expect.any(String), { signal });
  });
});
