import { describe, expect, it, vi } from 'vitest';

import { CloudflareProvider } from './cloudflare.js';

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00]);

function cfJson(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), { status, headers: { 'content-type': 'application/json' } });
}

const ENV = {
  CLOUDFLARE_ACCOUNT_ID: 'acct-123',
  CLOUDFLARE_API_TOKEN: 'token-abc',
};

describe('CloudflareProvider', () => {
  it('reports configured from the environment', () => {
    expect(new CloudflareProvider({ env: ENV }).configured).toBe(true);
    expect(new CloudflareProvider({ env: {} }).configured).toBe(false);
  });

  it('reports a config help hint when unconfigured', () => {
    expect(new CloudflareProvider({ env: {} }).configHelp).toContain('CLOUDFLARE_ACCOUNT_ID');
  });

  it('lists the img2img model', async () => {
    const provider = new CloudflareProvider({ env: ENV });
    await expect(provider.listModels()).resolves.toEqual(['@cf/runwayml/stable-diffusion-v1-5-img2img']);
  });

  it('posts prompt and base64 image and decodes the result', async () => {
    const fetchImpl = vi.fn(async () => cfJson({ success: true, result: { image: PNG.toString('base64') } }));
    const provider = new CloudflareProvider({ env: ENV, fetchImpl: fetchImpl as unknown as typeof fetch });
    const result = await provider.generate({
      prompt: 'watercolor version',
      width: 512,
      height: 384,
      seed: 7,
      referenceImage: { kind: 'dataUrl', dataUrl: 'data:image/png;base64,aGVsbG8=' },
    });

    const [url, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(
      'https://api.cloudflare.com/client/v4/accounts/acct-123/ai/run/@cf/runwayml/stable-diffusion-v1-5-img2img',
    );
    const headers = init.headers as Record<string, string>;
    expect(headers.authorization).toBe('Bearer token-abc');
    const body = JSON.parse(init.body as string) as Record<string, unknown>;
    expect(body.prompt).toBe('watercolor version');
    expect(body.image_b64).toBe('aGVsbG8=');
    expect(body.width).toBe(512);
    expect(body.height).toBe(384);
    expect(body.seed).toBe(7);

    expect(result.provider).toBe('cloudflare');
    expect(result.contentType).toBe('image/png');
    expect(result.bytes).toEqual(PNG);
  });

  it('throws when not configured', async () => {
    const provider = new CloudflareProvider({ env: {} });
    await expect(provider.generate({ prompt: 'x', referenceImage: { kind: 'dataUrl', dataUrl: 'data:image/png;base64,aA==' } })).rejects.toThrow(
      /not configured/,
    );
  });

  it('surfaces API errors', async () => {
    const fetchImpl = vi.fn(async () =>
      cfJson({ success: false, errors: [{ message: 'account suspended' }], result: null }, 400),
    );
    const provider = new CloudflareProvider({ env: ENV, fetchImpl: fetchImpl as unknown as typeof fetch });
    await expect(
      provider.generate({ prompt: 'x', referenceImage: { kind: 'dataUrl', dataUrl: 'data:image/png;base64,aA==' } }),
    ).rejects.toThrow(/account suspended/);
  });
});
