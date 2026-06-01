import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

function normalizeBasePath(rawValue) {
  const value = String(rawValue || '').trim();
  if (!value || value === '/') {
    return '/';
  }
  return `/${value.replace(/^\/+|\/+$/g, '')}/`;
}

const appBase = normalizeBasePath(process.env.VITE_APP_BASE || process.env.AAIS_APP_BASE);

export default defineConfig({
  base: appBase,
  plugins: [react()],
  envPrefix: ['VITE_', 'REACT_APP_'],
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    fs: {
      allow: ['..'],
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
  },
  build: {
    outDir: 'build',
    emptyOutDir: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      reportsDirectory: './coverage',
      exclude: [
        'build/**',
        'coverage/**',
        'node_modules/**',
        'scripts/**',
      ],
    },
  },
});
