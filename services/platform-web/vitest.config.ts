import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig } from 'vitest/config';

const serviceDir = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  test: {
    include: ['lib/**/*.test.ts'],
    environment: 'node',
  },
  resolve: {
    alias: {
      '@aaes-os/sovereignx-router': path.join(serviceDir, '../../packages/sovereignx-router/src/pricing.ts'),
    },
  },
});
