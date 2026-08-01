import { describe, expect, it } from 'vitest';

import { createAvailableProviders, pickProvider } from './registry.js';

describe('provider registry', () => {
  it('creates pollinations, cloudflare, and huggingface providers', () => {
    const providers = createAvailableProviders({ env: {} });
    expect(providers.map((provider) => provider.name)).toEqual(['pollinations', 'cloudflare', 'huggingface']);
  });

  it('marks providers configured from the environment', () => {
    const providers = createAvailableProviders({
      env: { CLOUDFLARE_ACCOUNT_ID: 'a', CLOUDFLARE_API_TOKEN: 't', HF_TOKEN: 'hf' },
    });
    expect(providers.every((provider) => provider.configured)).toBe(true);
  });

  it('picks the first configured provider by default', () => {
    const providers = createAvailableProviders({ env: { HF_TOKEN: 'hf' } });
    expect(pickProvider(providers, undefined).name).toBe('pollinations');
    const onlyPollinations = createAvailableProviders({ env: {} });
    expect(pickProvider(onlyPollinations, undefined).name).toBe('pollinations');
  });

  it('picks a provider by name', () => {
    const providers = createAvailableProviders({ env: {} });
    expect(pickProvider(providers, 'cloudflare').name).toBe('cloudflare');
    expect(pickProvider(providers, 'huggingface').name).toBe('huggingface');
  });

  it('throws for unknown provider names', () => {
    const providers = createAvailableProviders({ env: {} });
    expect(() => pickProvider(providers, 'nope')).toThrow(/Unknown provider/);
  });
});
