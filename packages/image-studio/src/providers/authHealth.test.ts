import { describe, expect, it } from 'vitest';

import { AuthHealthChecker } from './authHealth.js';
import type { ImageProvider, ProviderEnv } from './types.js';

const mockProviders: ImageProvider[] = [
  {
    name: 'pollinations',
    requiresApiKey: false,
    configured: true,
    configHelp: '',
    listModels: async () => ['sana'],
    generate: async () => ({ provider: 'pollinations', model: 'sana', contentType: 'image/png', bytes: Buffer.from([]) }),
  },
  {
    name: 'genblaze',
    requiresApiKey: true,
    configured: true,
    configHelp: 'Genblaze media server',
    listModels: async () => ['mrs-scene-spec'],
    generate: async () => ({ provider: 'genblaze', model: 'mrs-scene-spec', contentType: 'image/png', bytes: Buffer.from([]) }),
  },
  {
    name: 'storyforge',
    requiresApiKey: true,
    configured: true,
    configHelp: 'StoryForge pipeline',
    listModels: async () => ['storyforge-full-pipeline'],
    generate: async () => ({ provider: 'storyforge', model: 'storyforge-full-pipeline', contentType: 'audio/wav', bytes: Buffer.from([]) }),
  },
  {
    name: 'cloudflare',
    requiresApiKey: true,
    configured: false,
    configHelp: 'Cloudflare requires CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN',
    listModels: async () => [],
    generate: async () => ({ provider: 'cloudflare', model: '', contentType: 'image/png', bytes: Buffer.from([]) }),
  },
  {
    name: 'huggingface',
    requiresApiKey: true,
    configured: true,
    configHelp: 'Hugging Face requires HF_TOKEN',
    listModels: async () => [],
    generate: async () => ({ provider: 'huggingface', model: '', contentType: 'image/png', bytes: Buffer.from([]) }),
  },
];

describe('AuthHealthChecker', () => {
  it('returns ready status for keyless providers', () => {
    const pollens = mockProviders.filter((p) => p.name === 'pollinations');
    const health = AuthHealthChecker.getAllProvidersHealth(pollens);
    expect(health[0].status).toBe('ready');
  });

  it('returns needs_auth for providers that require API keys but have none set', () => {
    const health = AuthHealthChecker.getAllProvidersHealth(mockProviders);
    const genblaze = health.find((h) => h.name === 'genblaze');
    const storyforge = health.find((h) => h.name === 'storyforge');
    expect(genblaze?.status).toBe('needs_auth');
    expect(storyforge?.status).toBe('needs_auth');
  });

  it('returns needs_auth for unconfigured providers', () => {
    const health = AuthHealthChecker.getAllProvidersHealth(mockProviders);
    const cloudflare = health.find((h) => h.name === 'cloudflare');
    expect(cloudflare?.status).toBe('needs_auth');
  });

  it('getAuthStatus returns correct env vars for genblaze', () => {
    const status = AuthHealthChecker.getAuthStatus('genblaze', {
      GENBLAZE_API_KEY: 'test-key',
      GENBLAZE_BASE_URL: 'http://localhost:8787',
    } as ProviderEnv);
    expect(status.envVars).toContain('GENBLAZE_API_KEY');
    expect(status.envVars).toContain('GENBLAZE_BASE_URL');
  });

  it('getAuthStatus returns correct env vars for storyforge', () => {
    const status = AuthHealthChecker.getAuthStatus('storyforge', {
      STORYFORGE_API_KEY: 'test-key',
      STORYFORGE_BASE_URL: 'http://localhost:8080',
    } as ProviderEnv);
    expect(status.envVars).toContain('STORYFORGE_API_KEY');
    expect(status.envVars).toContain('STORYFORGE_BASE_URL');
  });

  it('getAuthStatus returns empty env vars for pollinations', () => {
    const status = AuthHealthChecker.getAuthStatus('pollinations');
    expect(status.envVars).toEqual([]);
    expect(status.hasApiKey).toBe(false);
  });

  it('getTokenFormat returns correct format for genblaze', () => {
    expect(AuthHealthChecker.getTokenFormat('genblaze')).toBe('Bearer token');
  });

  it('getTokenFormat returns correct format for storyforge', () => {
    expect(AuthHealthChecker.getTokenFormat('storyforge')).toBe('Bearer token');
  });

  it('generateHealthReport produces a readable report', () => {
    const health = AuthHealthChecker.getAllProvidersHealth(mockProviders);
    const report = AuthHealthChecker.generateHealthReport(health);
    expect(report).toContain('Provider Health Report');
    expect(report).toContain('Total Providers: 5');
  });

  it('getHealthyProviders filters correctly', () => {
    const health = AuthHealthChecker.getAllProvidersHealth(mockProviders);
    const healthy = AuthHealthChecker.getHealthyProviders(health);
    const pollinations = healthy.find((h) => h.name === 'pollinations');
    expect(pollinations).toBeDefined();
  });

  it('getUnconfiguredProviders filters correctly', () => {
    const health = AuthHealthChecker.getAllProvidersHealth(mockProviders);
    const needsAuth = AuthHealthChecker.getUnconfiguredProviders(health);
    const names = needsAuth.map((h) => h.name);
    expect(names).toContain('genblaze');
    expect(names).toContain('storyforge');
    expect(names).toContain('cloudflare');
  });
});