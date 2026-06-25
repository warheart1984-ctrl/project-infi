/**
 * AUTO-GENERATED — do not edit by hand.
 * Regenerate: pnpm sdk:generate
 */
import createClient from 'openapi-fetch';

import type { paths } from './types.js';

export type { components, paths, operations } from './types.js';

export interface CasClientOptions {
  baseUrl: string;
  apiKey?: string;
}

export function createCasClient(options: CasClientOptions) {
  return createClient<paths>({
    baseUrl: options.baseUrl,
    headers: options.apiKey
      ? { Authorization: `Bearer ${options.apiKey}` }
      : undefined,
  });
}

/** Default client using AAES_RUNTIME_URL when set. */
export const client = createCasClient({
  baseUrl: process.env.AAES_RUNTIME_URL ?? 'http://localhost:8787',
});
