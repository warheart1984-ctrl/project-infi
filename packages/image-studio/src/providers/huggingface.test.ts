import { describe, expect, it, vi } from 'vitest';

import { HuggingFaceProvider } from './huggingface.js';

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00]);
const ENV = { HF_TOKEN: 'hf_test' };

describe('HuggingFaceProvider', () => {
  it('reports configured from the environment', () => {
    expect(new HuggingFaceProvider({ env: ENV }).configured).toBe(true);
    expect(new HuggingFaceProvider({ env: {} }).configured).toBe(false);
  });

  it('lists the default img2img model', async () => {
    const provider = new HuggingFaceProvider({ env: ENV });
    await expect(provider.listModels()).resolves.toEqual(['black-forest-labs/FLUX.1-Kontext-dev']);
  });

  it('posts base64 inputs and parameters and returns the image bytes', async () => {
    const fetchImpl = vi.fn(async () => new Response(new Blob([new Uint8Array(PNG)]), { status: 200, headers: { 'content-type': 'image/png' } }));
    const provider = new HuggingFaceProvider({ env: ENV, fetchImpl: fetchImpl as unknown as typeof fetch });
    const result = await provider.generate({
      prompt: 'watercolor version',
      width: 768,
      height: 512,
      referenceImage: { kind: 'dataUrl', dataUrl: 'data:image/png;base64,aGVsbG8=' },
    });

    const [url, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(
      'https://router.huggingface.co/hf-inference/models/black-forest-labs%2FFLUX.1-Kontext-dev/image-to-image',
    );
    const headers = init.headers as Record<string, string>;
    expect(headers.authorization).toBe('Bearer hf_test');
    const body = JSON.parse(init.body as string) as { inputs: string; parameters: { prompt: string; target_size: { width: number; height: number } } };
    expect(body.inputs).toBe('aGVsbG8=');
    expect(body.parameters.prompt).toBe('watercolor version');
    expect(body.parameters.target_size).toEqual({ width: 768, height: 512 });

    expect(result.provider).toBe('huggingface');
    expect(result.model).toBe('black-forest-labs/FLUX.1-Kontext-dev');
    expect(result.contentType).toBe('image/png');
    expect(result.bytes).toEqual(PNG);
  });

  it('honors a custom model override', async () => {
    const fetchImpl = vi.fn(async () => new Response(new Blob([new Uint8Array(PNG)]), { status: 200 }));
    const provider = new HuggingFaceProvider({ env: ENV, fetchImpl: fetchImpl as unknown as typeof fetch });
    await provider.generate({ prompt: 'x', model: 'some/user/img2img-model', referenceImage: { kind: 'dataUrl', dataUrl: 'data:image/png;base64,aA==' } });
    const [url] = fetchImpl.mock.calls[0] as [string];
    expect(url).toContain('/some%2Fuser%2Fimg2img-model/image-to-image');
  });

  it('throws when not configured', async () => {
    const provider = new HuggingFaceProvider({ env: {} });
    await expect(provider.generate({ prompt: 'x', referenceImage: { kind: 'dataUrl', dataUrl: 'data:image/png;base64,aA==' } })).rejects.toThrow(
      /not configured/,
    );
  });

  it('surfaces API errors', async () => {
    const fetchImpl = vi.fn(async () => new Response('{"error":"model too busy"}', { status: 503 }));
    const provider = new HuggingFaceProvider({ env: ENV, fetchImpl: fetchImpl as unknown as typeof fetch });
    await expect(
      provider.generate({ prompt: 'x', referenceImage: { kind: 'dataUrl', dataUrl: 'data:image/png;base64,aA==' } }),
    ).rejects.toThrow(/503/);
  });
});
