import { CloudflareProvider } from './cloudflare.js';
import { GenblazeProvider } from './genblaze.js';
import { HfSpaceProvider } from './hfspace.js';
import { HuggingFaceProvider } from './huggingface.js';
import { PollinationsProvider } from './pollinations.js';
import { StoryForgeProvider } from './storyforge.js';
import type { ImageProvider, ProviderEnv } from './types.js';

export interface ProviderRegistryOptions {
  env?: ProviderEnv;
  fetchImpl?: typeof fetch;
}

export function createAvailableProviders(options: ProviderRegistryOptions = {}): ImageProvider[] {
  const env = options.env ?? (process.env as ProviderEnv);
  const fetchImpl = options.fetchImpl ?? fetch;
return [
    new PollinationsProvider(undefined, fetchImpl),
    new GenblazeProvider({ env, fetchImpl }),
    new StoryForgeProvider({ env, fetchImpl }),
    new CloudflareProvider({ env, fetchImpl }),
    new HuggingFaceProvider({ env, fetchImpl }),
    new HfSpaceProvider({ fetchImpl }),
  ];
}

export function pickProvider(
  providers: readonly ImageProvider[],
  name: string | undefined,
): ImageProvider {
  if (!name) {
    const firstConfigured = providers.find((provider) => provider.configured);
    return firstConfigured ?? providers[0];
  }
  const match = providers.find((provider) => provider.name === name);
  if (!match) {
    throw new Error(`Unknown provider "${name}". Available: ${providers.map((provider) => provider.name).join(', ')}`);
  }
  return match;
}
