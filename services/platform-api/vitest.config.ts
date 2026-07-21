import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const svcDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/platform-core': path.join(svcDir, '../../packages/platform-core/src/index.ts'),
      '@aaes-os/platform-sdk': path.join(svcDir, '../../packages/platform-sdk/src/index.ts'),
      '@aaes-os/psom-mesh': path.join(svcDir, '../../packages/psom-mesh/src/index.ts'),
      '@aaes-os/sgce': path.join(svcDir, '../../packages/sgce/src/index.ts'),
      '@aaes-os/governed-runtime': path.join(svcDir, '../../packages/governed-runtime/src/index.ts'),
      '@aaes-os/federation': path.join(svcDir, '../../packages/federation/src/index.ts'),
      '@aaes-os/aaes-governance': path.join(svcDir, '../../packages/aaes-governance/src/index.ts'),
      '@aaes-os/sovren': path.join(svcDir, '../../packages/sovren/src/index.ts'),
      '@aaes-os/lirl': path.join(svcDir, '../../packages/lirl/src/index.ts'),
      '@aaes-os/runledger': path.join(svcDir, '../../packages/runledger/src/index.ts'),
      '@aaes-os/evidence-receipts': path.join(svcDir, '../../packages/evidence-receipts/src/index.ts'),
      '@aaes-os/sovereignx-router': path.join(svcDir, 'src/sovereignx-router.vitest.ts'),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
});
