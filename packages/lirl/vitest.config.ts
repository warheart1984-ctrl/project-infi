import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/aaes-governance': path.join(rootDir, 'packages/aaes-governance/src/index.ts'),
      '@aaes-os/evidence-receipts': path.join(rootDir, 'packages/evidence-receipts/src/index.ts'),
      '@aaes-os/runledger': path.join(rootDir, 'packages/runledger/src/index.ts'),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
});
