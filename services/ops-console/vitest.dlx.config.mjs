export default {
  resolve: {
    alias: {
      '@aaes-os/aaes-governance': new URL('../../packages/aaes-governance/src/index.ts', import.meta.url).pathname,
      '@aaes-os/runledger': new URL('../../packages/runledger/src/index.ts', import.meta.url).pathname,
      '@aaes-os/trace-bus': new URL('../../packages/trace-bus/src/index.ts', import.meta.url).pathname,
      '@aaes-os/ucr-runtime': new URL('../../packages/ucr-runtime/src/index.ts', import.meta.url).pathname,
      '@aaes-os/mri-instrument': new URL('../../packages/mri-instrument/src/index.ts', import.meta.url).pathname,
      '@aaes-os/tri-core-protocol': new URL('../../packages/tri-core-protocol/src/index.ts', import.meta.url).pathname,
    },
  },
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
};
