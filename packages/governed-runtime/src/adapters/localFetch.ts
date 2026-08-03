import { Agent, fetch as undiciFetch } from 'undici';

/** Long timeouts for local free models (Ollama cold-load can exceed undici defaults). */
const LOCAL_AGENT = new Agent({
  connectTimeout: 60_000,
  headersTimeout: 15 * 60_000,
  bodyTimeout: 15 * 60_000,
});

/**
 * fetch() with extended undici timeouts suitable for Ollama / LM Studio.
 */
export function createLocalFetch(): typeof globalThis.fetch {
  const localFetch: typeof globalThis.fetch = (input, init) => {
    return undiciFetch(input as Parameters<typeof undiciFetch>[0], {
      ...(init as object),
      dispatcher: LOCAL_AGENT,
    }) as unknown as ReturnType<typeof globalThis.fetch>;
  };
  return localFetch;
}

export async function warmOllamaModel(
  baseUrl: string,
  model: string,
  fetchImpl: typeof globalThis.fetch = createLocalFetch(),
): Promise<void> {
  const url = `${baseUrl.replace(/\/$/, '')}/api/generate`;
  const res = await fetchImpl(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model,
      prompt: '',
      keep_alive: '30m',
      stream: false,
    }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`Ollama warm-up failed (${res.status}): ${detail}`);
  }
  await res.json().catch(() => undefined);
}
