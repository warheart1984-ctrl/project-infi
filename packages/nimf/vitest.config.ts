import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

export default defineConfig({
  resolve: { alias: { '@aaes-os/mri-instrument': path.join(rootDir, 'packages/mri-instrument/src/index.ts') } },
  test: { include: ['src/**/*.test.ts'], environment: 'node' },
});
