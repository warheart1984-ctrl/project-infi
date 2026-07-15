#!/usr/bin/env tsx
import { existsSync } from 'node:fs';
import path from 'node:path';
import { loadEnvFile } from 'node:process';

const envCandidates = [
  process.env.PLATFORM_ENV_FILE,
  path.resolve(process.cwd(), '.env'),
  path.resolve(process.cwd(), '..', '..', '.env'),
].filter((value): value is string => Boolean(value));

for (const candidate of envCandidates) {
  if (existsSync(candidate)) {
    loadEnvFile(candidate);
    break;
  }
}

const { createApp } = await import('./server.js');

const PORT = Number(process.env.PLATFORM_API_PORT ?? 4100);
const app = createApp();
app.listen(PORT, () => {
  console.log(`Platform API listening on http://localhost:${PORT}`);
});
