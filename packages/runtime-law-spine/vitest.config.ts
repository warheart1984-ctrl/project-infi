import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/trust-root': path.join(rootDir, 'packages/trust-root/src/index.ts'),
      '@aaes-os/ucr-attestation': path.join(rootDir, 'packages/ucr-attestation/src/index.ts'),
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
});
