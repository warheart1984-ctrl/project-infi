import { describe, expect, it, vi } from 'vitest';

import { HF_SPACE_BASE_URL, HfSpaceProvider } from './hfspace.js';

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00]);

function sseWithImage(eventId: string): string {
  return [
    'event: generating',
    'data: [[{"image": {"path": "/tmp/gradio/abc/out.png", "url": "' +
      `${HF_SPACE_BASE_URL}/gradio_api/file=/tmp/gradio/abc/out.png` +
      '", "mime_type": "image/png", "meta": {"_type": "gradio.FileData"}}, "caption": null}], "42"]',
    '',
    'event: complete',
    'data: [[{"image": {"path": "/tmp/gradio/abc/out.png", "url": "' +
      `${HF_SPACE_BASE_URL}/gradio_api/file=/tmp/gradio/abc/out.png` +
      '", "mime_type": "image/png", "meta": {"_type": "gradio.FileData"}}, "caption": null}], "42"]',
    '',
  ].join('\n');
}

describe('HfSpaceProvider', () => {
  it('is keyless and always configured', () => {
    const provider = new HfSpaceProvider();
    expect(provider.requiresApiKey).toBe(false);
    expect(provider.configured).toBe(true);
    expect(provider.configHelp).toContain('ZeroGPU');
  });

  it('lists the Space model', async () => {
    await expect(new HfSpaceProvider().listModels()).resolves.toEqual(['FLUX.2-Klein-9B']);
  });

  it('uploads a dataUrl base image, starts inference, polls, and downloads the result', async () => {
    const uploadResponse = new Response(JSON.stringify(['/tmp/gradio/up/input.png']), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const startResponse = new Response(JSON.stringify({ event_id: 'evt-1' }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const pollResponse = new Response(sseWithImage('evt-1'), {
      status: 200,
      headers: { 'content-type': 'text/event-stream' },
    });
    const downloadResponse = new Response(new Uint8Array(PNG), {
      status: 200,
      headers: { 'content-type': 'image/png' },
    });
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(uploadResponse)
      .mockResolvedValueOnce(startResponse)
      .mockResolvedValueOnce(pollResponse)
      .mockResolvedValueOnce(downloadResponse);

    const provider = new HfSpaceProvider({ fetchImpl: fetchImpl as unknown as typeof fetch });
    const result = await provider.generate({
      prompt: 'oil painting of a red square',
      seed: 7,
      referenceImage: { kind: 'dataUrl', dataUrl: 'data:image/png;base64,aGVsbG8=' },
    });

    expect(fetchImpl).toHaveBeenCalledTimes(4);
    const [uploadUrl, uploadInit] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(uploadUrl).toBe(`${HF_SPACE_BASE_URL}/gradio_api/upload`);
    expect(uploadInit.method).toBe('POST');
    expect(uploadInit.body).toBeInstanceOf(FormData);

    const [startUrl, startInit] = fetchImpl.mock.calls[1] as [string, RequestInit];
    expect(startUrl).toBe(`${HF_SPACE_BASE_URL}/gradio_api/call/infer`);
    const body = JSON.parse(startInit.body as string) as { data: unknown[] };
    expect(body.data).toHaveLength(27);
    expect(body.data[0]).toEqual({ path: '/tmp/gradio/up/input.png' });
    expect(body.data[2]).toBe('oil painting of a red square');
    expect(body.data[6]).toBe(7);

    const [pollUrl] = fetchImpl.mock.calls[2] as [string];
    expect(pollUrl).toBe(`${HF_SPACE_BASE_URL}/gradio_api/call/infer/evt-1`);

    expect(result.provider).toBe('hfspace');
    expect(result.model).toBe('FLUX.2-Klein-9B');
    expect(result.contentType).toBe('image/png');
    expect(result.bytes).toEqual(PNG);
  });

  it('passes a hosted URL straight through as the base image without uploading', async () => {
    const startResponse = new Response(JSON.stringify({ event_id: 'evt-2' }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const pollResponse = new Response(sseWithImage('evt-2'), {
      status: 200,
      headers: { 'content-type': 'text/event-stream' },
    });
    const downloadResponse = new Response(new Uint8Array(PNG), {
      status: 200,
      headers: { 'content-type': 'image/png' },
    });
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(startResponse)
      .mockResolvedValueOnce(pollResponse)
      .mockResolvedValueOnce(downloadResponse);

    const provider = new HfSpaceProvider({ fetchImpl: fetchImpl as unknown as typeof fetch });
    await provider.generate({
      prompt: 'portrait',
      referenceImage: { kind: 'url', url: 'https://example.com/photo.png' },
    });

    expect(fetchImpl).toHaveBeenCalledTimes(3);
    const [startUrl, startInit] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(startUrl).toBe(`${HF_SPACE_BASE_URL}/gradio_api/call/infer`);
    const body = JSON.parse(startInit.body as string) as { data: unknown[] };
    expect(body.data[0]).toEqual({ url: 'https://example.com/photo.png' });
    expect(body.data[11]).toBe('Auto (from base image)');
  });

  it('uses Custom canvas mode and clamps requested dimensions', async () => {
    const startResponse = new Response(JSON.stringify({ event_id: 'evt-3' }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const pollResponse = new Response(sseWithImage('evt-3'), {
      status: 200,
      headers: { 'content-type': 'text/event-stream' },
    });
    const downloadResponse = new Response(new Uint8Array(PNG), {
      status: 200,
      headers: { 'content-type': 'image/png' },
    });
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(startResponse)
      .mockResolvedValueOnce(pollResponse)
      .mockResolvedValueOnce(downloadResponse);

    const provider = new HfSpaceProvider({ fetchImpl: fetchImpl as unknown as typeof fetch });
    await provider.generate({
      prompt: 'wide',
      width: 9999,
      height: 128,
      referenceImage: { kind: 'url', url: 'https://example.com/photo.png' },
    });

    const [_, startInit] = fetchImpl.mock.calls[0] as [string, RequestInit];
    const body = JSON.parse(startInit.body as string) as { data: unknown[] };
    expect(body.data[11]).toBe('Custom');
    expect(body.data[12]).toBe(2048);
    expect(body.data[13]).toBe(512);
  });

  it('requires a reference image', async () => {
    const provider = new HfSpaceProvider();
    await expect(provider.generate({ prompt: 'x' })).rejects.toThrow(/requires a base image/);
  });

  it('surfaces inference errors reported by the Space', async () => {
    const startResponse = new Response(JSON.stringify({ event_id: 'evt-4' }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const pollResponse = new Response('event: error\ndata: {"error": "out of GPU quota", "visible": true}\n\n', {
      status: 200,
      headers: { 'content-type': 'text/event-stream' },
    });
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(startResponse)
      .mockResolvedValueOnce(pollResponse);

    const provider = new HfSpaceProvider({ fetchImpl: fetchImpl as unknown as typeof fetch });
    await expect(
      provider.generate({
        prompt: 'x',
        referenceImage: { kind: 'url', url: 'https://example.com/photo.png' },
      }),
    ).rejects.toThrow(/out of GPU quota/);
  });

  it('throws when inference finishes without an image', async () => {
    const startResponse = new Response(JSON.stringify({ event_id: 'evt-5' }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const pollResponse = new Response(
      'event: complete\ndata: [[], "42"]\n\n',
      { status: 200, headers: { 'content-type': 'text/event-stream' } },
    );
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(startResponse)
      .mockResolvedValueOnce(pollResponse);

    const provider = new HfSpaceProvider({ fetchImpl: fetchImpl as unknown as typeof fetch });
    await expect(
      provider.generate({
        prompt: 'x',
        referenceImage: { kind: 'url', url: 'https://example.com/photo.png' },
      }),
    ).rejects.toThrow(/finished without producing an image/);
  });
});
