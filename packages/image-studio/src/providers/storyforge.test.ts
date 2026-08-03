import { describe, expect, it, vi } from 'vitest';

import { StoryForgeProvider } from './storyforge.js';

const PNG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00, 0x00]);

describe('StoryForgeProvider', () => {
  it('is keyless and always configured', () => {
    const provider = new StoryForgeProvider();
    expect(provider.requiresApiKey).toBe(true);
    expect(provider.configured).toBe(true);
    expect(provider.configHelp).toContain('StoryForge pipeline');
  });

  it('lists pipeline models', async () => {
    const models = await new StoryForgeProvider().listModels();
    expect(models).toEqual([
      'storyforge-full-pipeline',
      'storyforge-text-only',
      'beatbox-audio',
      'speakers-tts',
    ]);
  });

  it('calls the three-stage pipeline and returns audio', async () => {
    const storyResponse = new Response(JSON.stringify({ narrative: 'A tale of a red tesseract.' }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const beatboxResponse = new Response(JSON.stringify({ audioUrl: 'http://localhost:8080/audio/beat.wav' }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const speakersResponse = new Response(JSON.stringify({ audioUrl: 'http://localhost:8080/audio/speech.wav' }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
    const audioResponse = new Response(new Uint8Array(PNG), { // using PNG bytes as audio placeholder
      status: 200,
      headers: { 'content-type': 'audio/wav' },
    });

    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(storyResponse)
      .mockResolvedValueOnce(beatboxResponse)
      .mockResolvedValueOnce(speakersResponse)
      .mockResolvedValueOnce(audioResponse);

    const provider = new StoryForgeProvider({ fetchImpl: fetchImpl as unknown as typeof fetch });
    const result = await provider.generate({ prompt: 'red tesseract adventure' });

    expect(fetchImpl).toHaveBeenCalledTimes(4);
    expect(fetchImpl.mock.calls[0][0]).toBe('http://127.0.0.1:8080/story/turn');
    expect(fetchImpl.mock.calls[1][0]).toBe('http://127.0.0.1:8080/beatbox/generate');
    expect(fetchImpl.mock.calls[2][0]).toBe('http://127.0.0.1:8080/speakers/synthesize');

    expect(result.provider).toBe('storyforge');
    expect(result.model).toBe('storyforge-full-pipeline');
    expect(result.contentType).toBe('audio/wav');
    expect(result.bytes).toEqual(PNG);
  });

  it('includes auth header when API key is set', async () => {
    const storyResponse = new Response(JSON.stringify({ narrative: 'x' }), { status: 200, headers: { 'content-type': 'application/json' } });
    const beatboxResponse = new Response(JSON.stringify({ audioUrl: 'http://localhost/a.wav' }), { status: 200, headers: { 'content-type': 'application/json' } });
    const speakersResponse = new Response(JSON.stringify({ audioUrl: 'http://localhost/b.wav' }), { status: 200, headers: { 'content-type': 'application/json' } });
    const audioResponse = new Response(new Uint8Array(PNG), { status: 200, headers: { 'content-type': 'audio/wav' } });

    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(storyResponse)
      .mockResolvedValueOnce(beatboxResponse)
      .mockResolvedValueOnce(speakersResponse)
      .mockResolvedValueOnce(audioResponse);

    const provider = new StoryForgeProvider({
      apiKey: 'sf-key',
      fetchImpl: fetchImpl as unknown as typeof fetch,
    });
    await provider.generate({ prompt: 'x' });

    const [, init] = fetchImpl.mock.calls[0] as [string, RequestInit];
    expect((init.headers as Record<string, string>).authorization).toBe('Bearer sf-key');
  });

  it('requires a non-empty prompt', async () => {
    const provider = new StoryForgeProvider();
    await expect(provider.generate({ prompt: '' })).rejects.toThrow(/non-empty prompt/);
  });
});