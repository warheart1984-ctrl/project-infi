import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const pkgDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/runledger': path.join(pkgDir, '../runledger/src/index.ts'),
      '@aaes-os/aaes-governance': path.join(pkgDir, './src/index.ts'),
      '@aaes-os/trace-bus': path.join(pkgDir, '../trace-bus/src/index.ts'),
      '@aaes-os/tri-core-protocol': path.join(pkgDir, '../tri-core-protocol/src/index.ts'),
      '@aaes-os/ucr-runtime': path.join(pkgDir, '../ucr-runtime/src/index.ts'),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
});
