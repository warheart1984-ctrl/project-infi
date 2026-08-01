import { describe, expect, it, vi } from 'vitest';

import { GenblazeProvider } from './genblaze.js';

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00]);

function genblazeSuccessResult(runId: string): object {
  return {
    schemaVersion: '1.0',
    requestId: runId,
    status: 'ok',
    provenance: {},
    routeUsed: 'scene-spec',
    artifacts: [
      {
        role: 'beauty-png',
        uri: `file:///output/${runId}-scene-spec.png`,
        sha256: 'abc123',
        mediaType: 'image/png',
      },
    ],
    mapping: { mappedTo: 'render-scene.mjs', statusTag: 'enforced' },
  };
}

describe('GenblazeProvider', () => {
  it('requires API key and is always configured', () => {
    const provider = new GenblazeProvider();
    expect(provider.requiresApiKey).toBe(true);
    expect(provider.configured).toBe(true);
    expect(provider.configHelp).toContain('Genblaze media server');
  });

  it('lists MRS route models', async () => {
    const models = await new GenblazeProvider().listModels();
    expect(models).toEqual([
      'mrs-scene-spec',
      'mrs-engine3d-still',
      'mrs-proton-raster',
      'mrs-rt4d',
    ]);
  });

  it('posts RenderRequest and downloads artifact', async () => {
    const runId = 'rr-test-123';
    const renderRequestResponse = new Response(JSON.stringify(genblazeSuccessResult(runId)), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const artifactResponse = new Response(new Uint8Array(PNG), {
      status: 200,
      headers: { 'content-type': 'image/png' },
    });
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(renderRequestResponse)
      .mockResolvedValueOnce(artifactResponse);

    const provider = new GenblazeProvider({ fetchImpl: fetchImpl as unknown as typeof fetch });
    const result = await provider.generate({
      prompt: 'a red tesseract',
      model: 'mrs-scene-spec',
    });

    expect(fetchImpl).toHaveBeenCalledTimes(2);
    const [url, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('http://127.0.0.1:8787/api/render-request');
    expect(init.method).toBe('POST');
    const body = JSON.parse(init.body as string) as { payload: { route: string } };
    expect(body.payload.route).toBe('scene-spec');

    const [previewUrl] = fetchImpl.mock.calls[1] as [string];
    expect(previewUrl).toBe(`http://127.0.0.1:8787/api/preview/${runId}`);

    expect(result.provider).toBe('genblaze');
    expect(result.model).toBe('mrs-scene-spec');
    expect(result.contentType).toBe('image/png');
    expect(result.bytes).toEqual(PNG);
  });

  it('surfaces non-ok responses', async () => {
    const errorResponse = new Response('server busy', { status: 503 });
    const fetchImpl = vi.fn().mockResolvedValueOnce(errorResponse);

    const provider = new GenblazeProvider({ fetchImpl: fetchImpl as unknown as typeof fetch });
    await expect(provider.generate({ prompt: 'x' })).rejects.toThrow(/Genblaze render-request failed \(503\)/);
  });

  it('requires a non-empty prompt', async () => {
    const provider = new GenblazeProvider();
    await expect(provider.generate({ prompt: '' })).rejects.toThrow(/non-empty prompt/);
  });

  it('includes auth header when API key is set', async () => {
    const renderResponse = new Response(JSON.stringify(genblazeSuccessResult('rr-auth-test')), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const artifactResponse = new Response(new Uint8Array(PNG), {
      status: 200,
      headers: { 'content-type': 'image/png' },
    });
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(renderResponse)
      .mockResolvedValueOnce(artifactResponse);

    const provider = new GenblazeProvider({
      apiKey: 'gb-key',
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });
    await provider.generate({ prompt: 'test' });

    const [, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect((init.headers as Record<string, string>).authorization).toBe('Bearer gb-key');
  });
});