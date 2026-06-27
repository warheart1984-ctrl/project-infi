import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/evidence-receipts': path.join(rootDir, 'packages/evidence-receipts/src/index.ts'),
      '@aaes-os/mri-instrument': path.join(rootDir, 'packages/mri-instrument/src/index.ts'),
      '@aaes-os/runtime-law-spine': path.join(rootDir, 'packages/runtime-law-spine/src/index.ts'),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
});
