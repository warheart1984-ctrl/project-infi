import type { ImageProvider, ProviderEnv } from './types.js';

/**
 * Provider health check utilities
 */

export interface ProviderHealthStatus {
  name: string;
  configured: boolean;
  authRequired: boolean;
  status: 'ready' | 'needs_auth' | 'unavailable' | 'error';
  error?: string;
  lastChecked?: number;
}

export interface AuthStatus {
  hasApiKey: boolean;
  envVars: string[];
  tokenFormat?: string;
}

export class AuthHealthChecker {
  private static readonly AUTH_VAR_MAP: Record<string, string[]> = {
    genblaze: ['GENBLAZE_API_KEY', 'GENBLAZE_BASE_URL'],
    storyforge: ['STORYFORGE_API_KEY', 'STORYFORGE_BASE_URL'],
    cloudflare: ['CLOUDFLARE_ACCOUNT_ID', 'CLOUDFLARE_API_TOKEN'],
    huggingface: ['HF_TOKEN'],
    pollinations: [],
    hfspace: [],
  };

  static getAuthStatus(providerName: string, env: ProviderEnv = process.env as ProviderEnv): AuthStatus {
    const varNames = this.AUTH_VAR_MAP[providerName] || [];
    const hasKeys = varNames.filter(varName => env[varName] && env[varName].trim() !== '');
    
    return {
      hasApiKey: hasKeys.length > 0,
      envVars: varNames.filter(varName => !!env[varName]),
      tokenFormat: this.getTokenFormat(providerName),
    };
  }

  private static getTokenFormat(providerName: string): string {
    const formats: Record<string, string> = {
      genblaze: 'Bearer token',
      storyforge: 'Bearer token',
      cloudflare: 'Account ID + API Token',
      huggingface: 'Hugging Face Inference Providers token (requires "Inference Providers" permission)',
    };
    return formats[providerName] || 'API key';
  }

  static getProviderHealth(provider: ImageProvider, authStatus: AuthStatus): ProviderHealthStatus {
    const status = this.determineStatus(provider, authStatus);
    
    return {
      name: provider.name,
      configured: provider.configured,
      authRequired: provider.requiresApiKey,
      status,
      error: status === 'error' ? this.getAuthError(provider.name, authStatus) : undefined,
      lastChecked: Date.now(),
    };
  }

  private static determineStatus(provider: ImageProvider, authStatus: AuthStatus): ProviderHealthStatus['status'] {
    if (!provider.configured) {
      return 'needs_auth';
    }
    
    if (provider.requiresApiKey && !authStatus.hasApiKey) {
      return 'needs_auth';
    }
    
    if (provider.name === 'genblaze' || provider.name === 'storyforge') {
      // For these providers, check if we can construct a valid URL
      try {
        const env = process.env as ProviderEnv;
        const baseUrl = env.GENBLAZE_BASE_URL || env.STORYFORGE_BASE_URL || 'http://127.0.0.1:8080';
        new URL(baseUrl);
        return 'ready';
      } catch {
        return 'error';
      }
    }
    
    return 'ready';
  }

  private static getAuthError(providerName: string, authStatus: AuthStatus): string {
    if (providerName === 'genblaze') {
      if (!authStatus.hasApiKey) {
        return 'GENBLAZE_API_KEY not set. Set GENBLAZE_API_KEY (Bearer token) or GENBLAZE_BASE_URL to your local Genblaze server.';
      }
      return 'Genblaze server unreachable or invalid endpoint';
    }
    
    if (providerName === 'storyforge') {
      if (!authStatus.hasApiKey) {
        return 'STORYFORGE_API_KEY not set. Set STORYFORGE_API_KEY (Bearer token) or STORYFORGE_BASE_URL to your Infinity service URL.';
      }
      return 'Infinity service unreachable or invalid endpoint';
    }
    
    if (providerName === 'cloudflare') {
      if (!authStatus.hasApiKey) {
        return 'CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN not set. Set these environment variables for Cloudflare provider.';
      }
      return 'Cloudflare API error - check account ID and token permissions';
    }
    
    if (providerName === 'huggingface') {
      if (!authStatus.hasApiKey) {
        return 'HF_TOKEN not set. Set HF_TOKEN with "Inference Providers" permission. Note: free tier serves no image-to-image models, requires paid subscription.';
      }
      return 'Hugging Face API error - token may be expired or missing required permissions';
    }
    
    return 'Provider configuration error';
  }

  static getAllProvidersHealth(
    providers: readonly ImageProvider[],
    env: ProviderEnv = process.env as ProviderEnv,
  ): ProviderHealthStatus[] {
    return providers.map(provider => {
      const authStatus = this.getAuthStatus(provider.name, env);
      return this.getProviderHealth(provider, authStatus);
    });
  }

  static getHealthyProviders(healthStatus: ProviderHealthStatus[]): ProviderHealthStatus[] {
    return healthStatus.filter(status => status.status === 'ready');
  }

  static getUnconfiguredProviders(healthStatus: ProviderHealthStatus[]): ProviderHealthStatus[] {
    return healthStatus.filter(status => status.status === 'needs_auth');
  }

  static generateHealthReport(healthStatus: ProviderHealthStatus[]): string {
    const healthy = this.getHealthyProviders(healthStatus);
    const needsAuth = this.getUnconfiguredProviders(healthStatus);
    
    let report = 'Provider Health Report\n';
    report += `Total Providers: ${healthStatus.length}\n`;
    report += `Ready: ${healthy.length}\n`;
    report += `Needs Setup: ${needsAuth.length}\n\n`;
    
    if (healthy.length > 0) {
      report += 'Healthy Providers:\n';
      healthy.forEach(provider => {
        report += `  ✓ ${provider.name}\n`;
      });
    }
    
    if (needsAuth.length > 0) {
      report += '\nProviders Requiring Configuration:\n';
      needsAuth.forEach(provider => {
        report += `  ⚠ ${provider.name}: ${provider.error}\n`;
      });
    }
    
    return report;
  }
}