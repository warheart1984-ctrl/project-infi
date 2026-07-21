import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const pkgDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/aais': path.join(pkgDir, '../aais/src/index.ts'),
      '@aaes-os/aaes-governance': path.join(pkgDir, '../aaes-governance/src/index.ts'),
      '@aaes-os/governed-runtime': path.join(pkgDir, '../governed-runtime/src/index.ts'),
      '@aaes-os/nova-shell': path.join(pkgDir, '../nova-shell/src/index.ts'),
      '@aaes-os/sovereignx-router': path.join(pkgDir, '../sovereignx-router/src/index.ts'),
      '@aaes-os/infinity-agents': path.join(pkgDir, '../infinity-agents/src/index.ts'),
      '@aaes-os/sandbox': path.join(pkgDir, '../sandbox/src/index.ts'),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
});
