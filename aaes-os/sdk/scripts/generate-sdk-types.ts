#!/usr/bin/env node
/**
 * Generates TypeScript types from the CAS 1.0 OpenAPI spec and writes a typed
 * openapi-fetch client wrapper.
 *
 * Run: pnpm sdk:generate
 */

import { execSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const openapiPath = path.join(__dirname, '../../api/cas-openapi.yaml');
const outDir = path.join(__dirname, '../generated');
const typesPath = path.join(outDir, 'types.ts');
const clientPath = path.join(outDir, 'client.ts');

execSync(`npx openapi-typescript "${openapiPath}" --output "${typesPath}"`, {
  stdio: 'inherit',
});

const clientSource = `/**
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
      ? { Authorization: \`Bearer \${options.apiKey}\` }
      : undefined,
  });
}

/** Default client using AAES_RUNTIME_URL when set. */
export const client = createCasClient({
  baseUrl: process.env.AAES_RUNTIME_URL ?? 'http://localhost:8787',
});
`;

writeFileSync(clientPath, clientSource, 'utf8');
console.log('SDK types + client generated at sdk/generated/');
