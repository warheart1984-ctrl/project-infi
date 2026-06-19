import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const serviceDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/aaes-governance': path.join(serviceDir, '../../packages/aaes-governance/src/index.ts'),
      '@aaes-os/runledger': path.join(serviceDir, '../../packages/runledger/src/index.ts'),
      '@aaes-os/trace-bus': path.join(serviceDir, '../../packages/trace-bus/src/index.ts'),
      '@aaes-os/ucr-runtime': path.join(serviceDir, '../../packages/ucr-runtime/src/index.ts'),
      '@aaes-os/tri-core-protocol': path.join(serviceDir, '../../packages/tri-core-protocol/src/index.ts'),
      '@aaes-os/mri-instrument': path.join(serviceDir, '../../packages/mri-instrument/src/index.ts'),
      '@aaes-os/trust-root': path.join(serviceDir, '../../packages/trust-root/src/index.ts'),
      '@aaes-os/ucr-attestation': path.join(serviceDir, '../../packages/ucr-attestation/src/index.ts'),
      '@aaes-os/runtime-law-spine': path.join(serviceDir, '../../packages/runtime-law-spine/src/index.ts'),
      '@aaes-os/evidence-receipts': path.join(serviceDir, '../../packages/evidence-receipts/src/index.ts'),
      '@aaes-os/constitutional-enforcement-node': path.join(serviceDir, '../../packages/constitutional-enforcement-node/src/index.ts'),
      '@aaes-os/meta-constitutional-calculus': path.join(serviceDir, '../../packages/meta-constitutional-calculus/src/index.ts'),
      '@aaes-os/transition-validation-pipeline': path.join(serviceDir, '../../packages/transition-validation-pipeline/src/index.ts'),
      '@aaes-os/sovereignty-ledger': path.join(serviceDir, '../../packages/sovereignty-ledger/src/index.ts'),
      '@aaes-os/invariant-registry': path.join(serviceDir, '../../packages/invariant-registry/src/index.ts'),
      '@aaes-os/nimf': path.join(serviceDir, '../../packages/nimf/src/index.ts'),
      '@aaes-os/constitutional-evolution': path.join(serviceDir, '../../packages/constitutional-evolution/src/index.ts'),
      '@aaes-os/omega-stress-harness': path.join(serviceDir, '../../packages/omega-stress-harness/src/index.ts'),
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
});
