import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const pkgDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/platform-core': path.join(pkgDir, '../platform-core/src/index.ts'),
      '@aaes-os/platform-sdk': path.join(pkgDir, '../platform-sdk/src/index.ts'),
      '@aaes-os/lirl': path.join(pkgDir, '../lirl/src/index.ts'),
      '@aaes-os/aaes-governance': path.join(pkgDir, '../aaes-governance/src/index.ts'),
      '@aaes-os/runledger': path.join(pkgDir, '../runledger/src/index.ts'),
      '@aaes-os/evidence-receipts': path.join(pkgDir, '../evidence-receipts/src/index.ts'),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
});
