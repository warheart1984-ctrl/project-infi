import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';

const operatorConfigEntry = fileURLToPath(new URL('../../packages/operator-config/src/index.ts', import.meta.url));
const coriAlphaSummaryEntry = fileURLToPath(new URL('../../packages/platform-core/src/coriAlphaSummary.tsx', import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@aaes-os/operator-config': operatorConfigEntry,
      '@aaes-os/platform-core/coriAlphaSummary': coriAlphaSummaryEntry,
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/telemetry': 'http://localhost:4000',
      '/readiness': 'http://localhost:4000',
      '/metrics': 'http://localhost:4000',
      '/mri': 'http://localhost:4000',
      '/cen': 'http://localhost:4000',
      '/pod': 'http://localhost:4000',
      '/patches': 'http://localhost:4000',
      '/sovereignty-ledger': 'http://localhost:4000',
      '/nimf': 'http://localhost:4000',
      '/evolution': 'http://localhost:4000',
      '/meta': 'http://localhost:4000',
      '/arena': 'http://localhost:4000',
    },
  },
  build: {
    outDir: 'dist/client',
    emptyOutDir: true,
  },
});
