import { defineConfig } from 'vitest/config';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

export default defineConfig({
  resolve: {
    alias: {
      '@aaes-os/constitutional-enforcement-node': path.join(rootDir, 'packages/constitutional-enforcement-node/src/index.ts'),
      '@aaes-os/sovereignty-ledger': path.join(rootDir, 'packages/sovereignty-ledger/src/index.ts'),
    },
  },
  test: { include: ['src/**/*.test.ts'], environment: 'node' },
});
