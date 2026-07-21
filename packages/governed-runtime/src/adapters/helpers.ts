import type { GovernedChatRequest, GovernedChatResponse } from '../types.js';

export interface OpenAiStyleResponse {
  choices?: Array<{ message?: { content?: string } }>;
  usage?: { prompt_tokens?: number; completion_tokens?: number };
}

export interface LocalApiResponse {
  text?: string;
  output?: string;
  tokensIn?: number;
  tokensOut?: number;
  latency?: number;
}

export function buildChatResponse(
  req: GovernedChatRequest,
  backendName: string,
  text: string,
  tokensIn: number,
  tokensOut: number,
  latencyMs = 0,
): GovernedChatResponse {
  return {
    intentId: req.intent.id,
    backendName,
    trace: req.trace,
    output: { text, tokensIn, tokensOut, latencyMs },
    governance: { policyIds: [], violations: [] },
  };
}

export async function postJson<T>(
  url: string,
  body: unknown,
  headers: Record<string, string> = {},
  fetchImpl: typeof globalThis.fetch = globalThis.fetch,
): Promise<T> {
  const res = await fetchImpl(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`Backend request failed (${res.status}): ${detail}`);
  }

  return (await res.json()) as T;
}
