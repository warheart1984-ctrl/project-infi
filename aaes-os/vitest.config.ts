import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/runledger': path.join(rootDir, 'packages/runledger/src/index.ts'),
      '@aaes-os/aaes-governance': path.join(rootDir, 'packages/aaes-governance/src/index.ts'),
      '@aaes-os/trace-bus': path.join(rootDir, 'packages/trace-bus/src/index.ts'),
      '@aaes-os/ucr-runtime': path.join(rootDir, 'packages/ucr-runtime/src/index.ts'),
      '@aaes-os/tri-core-protocol': path.join(rootDir, 'packages/tri-core-protocol/src/index.ts'),
      '@aaes-os/mri-instrument': path.join(rootDir, 'packages/mri-instrument/src/index.ts'),
      '@aaes-os/trust-root': path.join(rootDir, 'packages/trust-root/src/index.ts'),
      '@aaes-os/ucr-attestation': path.join(rootDir, 'packages/ucr-attestation/src/index.ts'),
      '@aaes-os/runtime-law-spine': path.join(rootDir, 'packages/runtime-law-spine/src/index.ts'),
      '@aaes-os/evidence-receipts': path.join(rootDir, 'packages/evidence-receipts/src/index.ts'),
      '@aaes-os/constitutional-enforcement-node': path.join(rootDir, 'packages/constitutional-enforcement-node/src/index.ts'),
      '@aaes-os/meta-constitutional-calculus': path.join(rootDir, 'packages/meta-constitutional-calculus/src/index.ts'),
      '@aaes-os/transition-validation-pipeline': path.join(rootDir, 'packages/transition-validation-pipeline/src/index.ts'),
      '@aaes-os/sovereignty-ledger': path.join(rootDir, 'packages/sovereignty-ledger/src/index.ts'),
      '@aaes-os/invariant-registry': path.join(rootDir, 'packages/invariant-registry/src/index.ts'),
      '@aaes-os/nimf': path.join(rootDir, 'packages/nimf/src/index.ts'),
      '@aaes-os/constitutional-evolution': path.join(rootDir, 'packages/constitutional-evolution/src/index.ts'),
      '@aaes-os/omega-stress-harness': path.join(rootDir, 'packages/omega-stress-harness/src/index.ts'),
    },
  },
  test: {
    include: ['tests/integration/**/*.test.ts', 'packages/**/src/**/*.test.ts', 'services/**/src/**/*.test.ts', 'services/**/src/**/*.test.tsx'],
    environment: 'node',
  },
});
