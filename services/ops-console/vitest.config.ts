import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';

const coriAlphaSummaryEntry = fileURLToPath(new URL('../../packages/platform-core/src/coriAlphaSummary.tsx', import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/aaes-governance': fileURLToPath(new URL('../../packages/aaes-governance/src/index.ts', import.meta.url)),
      '@aaes-os/runledger': fileURLToPath(new URL('../../packages/runledger/src/index.ts', import.meta.url)),
      '@aaes-os/trace-bus': fileURLToPath(new URL('../../packages/trace-bus/src/index.ts', import.meta.url)),
      '@aaes-os/ucr-runtime': fileURLToPath(new URL('../../packages/ucr-runtime/src/index.ts', import.meta.url)),
      '@aaes-os/tri-core-protocol': fileURLToPath(new URL('../../packages/tri-core-protocol/src/index.ts', import.meta.url)),
      '@aaes-os/mri-instrument': fileURLToPath(new URL('../../packages/mri-instrument/src/index.ts', import.meta.url)),
      '@aaes-os/trust-root': fileURLToPath(new URL('../../packages/trust-root/src/index.ts', import.meta.url)),
      '@aaes-os/ucr-attestation': fileURLToPath(new URL('../../packages/ucr-attestation/src/index.ts', import.meta.url)),
      '@aaes-os/runtime-law-spine': fileURLToPath(new URL('../../packages/runtime-law-spine/src/index.ts', import.meta.url)),
      '@aaes-os/evidence-receipts': fileURLToPath(new URL('../../packages/evidence-receipts/src/index.ts', import.meta.url)),
      '@aaes-os/constitutional-enforcement-node': fileURLToPath(new URL('../../packages/constitutional-enforcement-node/src/index.ts', import.meta.url)),
      '@aaes-os/meta-constitutional-calculus': fileURLToPath(new URL('../../packages/meta-constitutional-calculus/src/index.ts', import.meta.url)),
      '@aaes-os/transition-validation-pipeline': fileURLToPath(new URL('../../packages/transition-validation-pipeline/src/index.ts', import.meta.url)),
      '@aaes-os/sovereignx-router': fileURLToPath(new URL('../../packages/sovereignx-router/src/index.ts', import.meta.url)),
      '@aaes-os/sovereignty-ledger': fileURLToPath(new URL('../../packages/sovereignty-ledger/src/index.ts', import.meta.url)),
      '@aaes-os/invariant-registry': fileURLToPath(new URL('../../packages/invariant-registry/src/index.ts', import.meta.url)),
      '@aaes-os/platform-core': fileURLToPath(new URL('../../packages/platform-core/src/index.ts', import.meta.url)),
      '@aaes-os/nimf': fileURLToPath(new URL('../../packages/nimf/src/index.ts', import.meta.url)),
      '@aaes-os/constitutional-evolution': fileURLToPath(new URL('../../packages/constitutional-evolution/src/index.ts', import.meta.url)),
      '@aaes-os/omega-stress-harness': fileURLToPath(new URL('../../packages/omega-stress-harness/src/index.ts', import.meta.url)),
      '@aaes-os/operator-config': fileURLToPath(new URL('../../packages/operator-config/src/index.ts', import.meta.url)),
      '@aaes-os/platform-core/coriAlphaSummary': coriAlphaSummaryEntry,
    },
  },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts', 'src/**/*.test.tsx'],
  },
});
