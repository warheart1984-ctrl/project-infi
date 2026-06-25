import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: [
      'tests/**/*.test.ts',
      'benchmarks/**/*.test.ts',
      'packages/**/src/**/*.test.ts',
    ],
  },
});
