import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const pkgDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/coda-doc': path.join(pkgDir, '../coda-doc/src/index.ts'),
      '@aaes-os/nova-coda': path.join(pkgDir, '../nova-coda/src/index.ts'),
      '@aaes-os/nova-substrate-client': path.join(pkgDir, '../nova-substrate-client/src/index.ts'),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
});
