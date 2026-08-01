import { describe, expect, it, vi } from 'vitest';

import { GeminiProvider } from './gemini.js';

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00]);

function geminiJson(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}

const ENV = { GEMINI_API_KEY: 'test-key' };

describe('GeminiProvider', () => {
  it('reports configured from GEMINI_API_KEY or GOOGLE_API_KEY', () => {
    expect(new GeminiProvider({ env: ENV }).configured).toBe(true);
    expect(new GeminiProvider({ env: { GOOGLE_API_KEY: 'g' } }).configured).toBe(true);
    expect(new GeminiProvider({ env: {} }).configured).toBe(false);
  });

  it('reports a config help hint when unconfigured', () => {
    expect(new GeminiProvider({ env: {} }).configHelp).toContain('GEMINI_API_KEY');
  });

  it('lists the default flash image model', async () => {
    const provider = new GeminiProvider({ env: ENV });
    const models = await provider.listModels();
    expect(models[0]).toBe('gemini-2.5-flash-image');
  });

  it('posts generateContent with responseModalities and decodes inline image', async () => {
    const fetchImpl = vi.fn(async () =>
      geminiJson({
        candidates: [
          {
            content: {
              parts: [
                { text: 'here you go' },
                { inlineData: { mimeType: 'image/png', data: PNG.toString('base64') } },
              ],
            },
          },
        ],
      }),
    );
    const provider = new GeminiProvider({ env: ENV, fetchImpl: fetchImpl as unknown as typeof fetch });
    const result = await provider.generate({ prompt: 'a red fox' });

    const [url, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(
      'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent',
    );
    const headers = init.headers as Record<string, string>;
    expect(headers['x-goog-api-key']).toBe('test-key');
    const body = JSON.parse(init.body as string) as {
      contents: Array<{ parts: Array<{ text?: string }> }>;
      generationConfig: { responseModalities: string[] };
    };
    expect(body.contents[0].parts[0].text).toBe('a red fox');
    expect(body.generationConfig.responseModalities).toEqual(['TEXT', 'IMAGE']);

    expect(result.provider).toBe('gemini');
    expect(result.model).toBe('gemini-2.5-flash-image');
    expect(result.contentType).toBe('image/png');
    expect(result.bytes).toEqual(PNG);
  });

  it('includes a dataUrl reference as inlineData', async () => {
    const fetchImpl = vi.fn(async () =>
      geminiJson({
        candidates: [
          {
            content: {
              parts: [{ inline_data: { mime_type: 'image/png', data: PNG.toString('base64') } }],
            },
          },
        ],
      }),
    );
    const provider = new GeminiProvider({ env: ENV, fetchImpl: fetchImpl as unknown as typeof fetch });
    await provider.generate({
      prompt: 'watercolor version',
      referenceImage: { kind: 'dataUrl', dataUrl: 'data:image/png;base64,aGVsbG8=' },
    });
    const body = JSON.parse((fetchImpl.mock.calls[0] as [string, RequestInit])[1].body as string) as {
      contents: Array<{ parts: Array<{ text?: string; inlineData?: { mimeType: string; data: string } }> }>;
    };
    expect(body.contents[0].parts).toHaveLength(2);
    expect(body.contents[0].parts[1].inlineData).toEqual({
      mimeType: 'image/png',
      data: 'aGVsbG8=',
    });
  });

  it('throws when not configured', async () => {
    const provider = new GeminiProvider({ env: {} });
    await expect(provider.generate({ prompt: 'x' })).rejects.toThrow(/not configured/);
  });

  it('throws on empty prompts', async () => {
    const provider = new GeminiProvider({ env: ENV });
    await expect(provider.generate({ prompt: '   ' })).rejects.toThrow(/non-empty prompt/);
  });

  it('surfaces API errors', async () => {
    const fetchImpl = vi.fn(async () =>
      geminiJson({ error: { message: 'quota exceeded', code: 429 } }, 429),
    );
    const provider = new GeminiProvider({ env: ENV, fetchImpl: fetchImpl as unknown as typeof fetch });
    await expect(provider.generate({ prompt: 'x' })).rejects.toThrow(/quota exceeded/);
  });

  it('throws when response has no image part', async () => {
    const fetchImpl = vi.fn(async () =>
      geminiJson({ candidates: [{ content: { parts: [{ text: 'sorry' }] } }] }),
    );
    const provider = new GeminiProvider({ env: ENV, fetchImpl: fetchImpl as unknown as typeof fetch });
    await expect(provider.generate({ prompt: 'x' })).rejects.toThrow(/no image/);
  });

  it('honors GEMINI_IMAGE_MODEL override', async () => {
    const fetchImpl = vi.fn(async () =>
      geminiJson({
        candidates: [
          { content: { parts: [{ inlineData: { mimeType: 'image/png', data: PNG.toString('base64') } }] } },
        ],
      }),
    );
    const provider = new GeminiProvider({
      env: { ...ENV, GEMINI_IMAGE_MODEL: 'gemini-2.0-flash-preview-image-generation' },
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });
    const result = await provider.generate({ prompt: 'cat' });
    expect(result.model).toBe('gemini-2.0-flash-preview-image-generation');
    expect((fetchImpl.mock.calls[0] as [string])[0]).toContain(
      'models/gemini-2.0-flash-preview-image-generation:generateContent',
    );
  });
});
