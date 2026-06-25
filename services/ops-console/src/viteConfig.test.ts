import { describe, expect, it } from 'vitest';

import viteConfig from '../vite.config.js';

describe('ops-console Vite proxy', () => {
  it('forwards every operator API path used by the React console', () => {
    const config = typeof viteConfig === 'function' ? viteConfig({ command: 'serve', mode: 'test' }) : viteConfig;
    const proxy = config.server?.proxy as Record<string, unknown>;

    expect(proxy).toEqual(expect.objectContaining({
      '/telemetry': expect.any(String),
      '/readiness': expect.any(String),
      '/mri': expect.any(String),
      '/cen': expect.any(String),
      '/pod': expect.any(String),
      '/patches': expect.any(String),
      '/sovereignty-ledger': expect.any(String),
      '/nimf': expect.any(String),
      '/evolution': expect.any(String),
      '/meta': expect.any(String),
    }));
  });
});
