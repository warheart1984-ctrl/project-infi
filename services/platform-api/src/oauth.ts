import { createHmac } from 'node:crypto';

import type { CustomerAuthProvider, CustomerLoginInput, CustomerSignupInput, GovernanceMode } from '@aaes-os/platform-core';

import { platform } from './state.js';

export type OAuthProvider = CustomerAuthProvider;

export interface OAuthAuthorizationContext {
  provider: OAuthProvider;
  mode: 'login' | 'signup';
  returnTo: string;
  redirectUri: string;
}

export interface OAuthCallbackResult {
  provider: OAuthProvider;
  mode: 'login' | 'signup';
  customer: ReturnType<typeof platform.signupCustomer>['customer'];
  session: ReturnType<typeof platform.signupCustomer>['session'];
  redirectTo: string;
}

type OAuthProviderConfig = {
  provider: OAuthProvider;
  authorizationUrl: string;
  tokenUrl: string;
  userInfoUrl?: string;
  scopes: string[];
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  extraAuthorizationParams?: Record<string, string>;
};

const PROVIDER_DEFINITIONS: Partial<Record<OAuthProvider, { label: string; authUrl: string; tokenUrl: string; userInfoUrl?: string; scopes: string[] }>> = {
  google: {
    label: 'Google',
    authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenUrl: 'https://oauth2.googleapis.com/token',
    userInfoUrl: 'https://openidconnect.googleapis.com/v1/userinfo',
    scopes: ['openid', 'email', 'profile'],
  },
  microsoft: {
    label: 'Microsoft',
    authUrl: 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
    tokenUrl: 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
    userInfoUrl: 'https://graph.microsoft.com/oidc/userinfo',
    scopes: ['openid', 'email', 'profile', 'offline_access'],
  },
  github: {
    label: 'GitHub',
    authUrl: 'https://github.com/login/oauth/authorize',
    tokenUrl: 'https://github.com/login/oauth/access_token',
    userInfoUrl: 'https://api.github.com/user',
    scopes: ['read:user', 'user:email'],
  },
  apple: {
    label: 'Apple',
    authUrl: 'https://appleid.apple.com/auth/authorize',
    tokenUrl: 'https://appleid.apple.com/auth/token',
    scopes: ['name', 'email'],
  },
};

function isOAuthProvider(value: string): value is OAuthProvider {
  return value === 'google' || value === 'microsoft' || value === 'github' || value === 'apple';
}

function normalizeProvider(value: string | undefined): OAuthProvider | null {
  if (!value) {
    return null;
  }
  return isOAuthProvider(value) ? value : null;
}

function encodeState(payload: Record<string, string>): string {
  const body = Buffer.from(JSON.stringify(payload), 'utf8').toString('base64url');
  const secret = process.env.PLATFORM_OAUTH_STATE_SECRET ?? 'platform-api-oauth-state';
  const signature = createHmac('sha256', secret).update(body).digest('base64url');
  return `${body}.${signature}`;
}

function decodeState(state: string): Record<string, string> | null {
  const [body, signature] = state.split('.');
  if (!body || !signature) {
    return null;
  }
  const secret = process.env.PLATFORM_OAUTH_STATE_SECRET ?? 'platform-api-oauth-state';
  const expected = createHmac('sha256', secret).update(body).digest('base64url');
  if (signature !== expected) {
    return null;
  }
  try {
    const raw = Buffer.from(body, 'base64url').toString('utf8');
    const parsed = JSON.parse(raw) as Record<string, string>;
    return parsed;
  } catch {
    return null;
  }
}

function providerConfig(provider: OAuthProvider, redirectUri: string): OAuthProviderConfig | null {
  const definition = PROVIDER_DEFINITIONS[provider];
  if (!definition) {
    return null;
  }
  const clientId = process.env[`${provider.toUpperCase()}_CLIENT_ID`] ?? '';
  const clientSecret = process.env[`${provider.toUpperCase()}_CLIENT_SECRET`] ?? '';
  const authorizationUrl = process.env[`${provider.toUpperCase()}_AUTHORIZATION_URL`] ?? definition.authUrl;
  const tokenUrl = process.env[`${provider.toUpperCase()}_TOKEN_URL`] ?? definition.tokenUrl;
  const userInfoUrl = process.env[`${provider.toUpperCase()}_USERINFO_URL`] ?? definition.userInfoUrl;
  if (!clientId || !clientSecret) {
    return null;
  }
  return {
    provider,
    authorizationUrl,
    tokenUrl,
    userInfoUrl,
    scopes: definition.scopes,
    clientId,
    clientSecret,
    redirectUri,
    extraAuthorizationParams:
      provider === 'microsoft'
        ? { prompt: 'select_account' }
        : provider === 'google'
          ? { prompt: 'select_account' }
          : provider === 'apple'
            ? { response_mode: 'form_post', response_type: 'code' }
            : undefined,
  };
}

export function listOAuthProviders() {
  return (Object.entries(PROVIDER_DEFINITIONS) as Array<[OAuthProvider, NonNullable<(typeof PROVIDER_DEFINITIONS)[OAuthProvider]>]>)
    .filter((entry): entry is [OAuthProvider, NonNullable<(typeof PROVIDER_DEFINITIONS)[OAuthProvider]>] => Boolean(entry[1]))
    .map(([provider, definition]) => ({
      provider,
      label: definition.label,
      configured: Boolean(process.env[`${provider.toUpperCase()}_CLIENT_ID`] && process.env[`${provider.toUpperCase()}_CLIENT_SECRET`]),
    }));
}

export function buildOAuthAuthorizationContext(provider: OAuthProvider, mode: 'login' | 'signup', returnTo: string): OAuthAuthorizationContext {
  const webBaseUrl = (process.env.PLATFORM_WEB_URL ?? 'http://localhost:3000').replace(/\/+$/, '');
  const redirectUri = `${webBaseUrl}/api/auth/oauth/${provider}/callback`;
  return {
    provider,
    mode,
    returnTo,
    redirectUri,
  };
}

export function buildOAuthStartPayload(provider: OAuthProvider, mode: 'login' | 'signup', returnTo: string) {
  const context = buildOAuthAuthorizationContext(provider, mode, returnTo);
  const config = providerConfig(provider, context.redirectUri);
  if (!config) {
    throw new Error(`OAUTH: provider ${provider} is not configured`);
  }
  const state = encodeState({
    provider,
    mode,
    returnTo: context.returnTo,
    redirectUri: context.redirectUri,
    issuedAt: new Date().toISOString(),
  });
  const params = new URLSearchParams({
    client_id: config.clientId,
    redirect_uri: config.redirectUri,
    response_type: 'code',
    scope: config.scopes.join(' '),
    state,
  });
  for (const [key, value] of Object.entries(config.extraAuthorizationParams ?? {})) {
    params.set(key, value);
  }
  return {
    provider,
    mode,
    state,
    redirectUri: config.redirectUri,
    authorizationUrl: `${config.authorizationUrl}?${params.toString()}`,
  };
}

async function exchangeCode(config: OAuthProviderConfig, code: string): Promise<Record<string, unknown>> {
  const body = new URLSearchParams({
    client_id: config.clientId,
    client_secret: config.clientSecret,
    code,
    grant_type: 'authorization_code',
    redirect_uri: config.redirectUri,
  });
  const response = await fetch(config.tokenUrl, {
    method: 'POST',
    headers: {
      accept: 'application/json',
      'content-type': 'application/x-www-form-urlencoded',
    },
    body: body.toString(),
  });
  if (!response.ok) {
    throw new Error(`OAUTH: token exchange failed for ${config.provider}`);
  }
  return response.json() as Promise<Record<string, unknown>>;
}

async function loadProfile(config: OAuthProviderConfig, tokenResponse: Record<string, unknown>): Promise<{
  email: string;
  displayName?: string;
  authSubject: string;
}> {
  const accessToken = String(tokenResponse.access_token ?? tokenResponse.accessToken ?? '');
  if (!accessToken) {
    throw new Error(`OAUTH: missing access token for ${config.provider}`);
  }

  if (config.provider === 'github') {
    const userRes = await fetch(config.userInfoUrl ?? 'https://api.github.com/user', {
      headers: {
        authorization: `Bearer ${accessToken}`,
        accept: 'application/vnd.github+json',
      },
    });
    if (!userRes.ok) {
      throw new Error('OAUTH: GitHub user lookup failed');
    }
    const user = (await userRes.json()) as { id?: number; login?: string; email?: string; name?: string };
    const email = user.email ?? `${user.login ?? 'github-user'}@users.noreply.github.com`;
    return {
      email,
      displayName: user.name ?? user.login ?? 'GitHub User',
      authSubject: `github:${user.id ?? user.login ?? email}`,
    };
  }

  if (!config.userInfoUrl) {
    const sub = String(tokenResponse.sub ?? tokenResponse.id_token ?? tokenResponse.access_token ?? tokenResponse.expires_in ?? '');
    return {
      email: String(tokenResponse.email ?? `${config.provider}-${sub || 'user'}@example.com`),
      displayName: String(tokenResponse.name ?? `${config.provider} user`),
      authSubject: `${config.provider}:${sub || emailFallback(tokenResponse, config.provider)}`,
    };
  }

  const userRes = await fetch(config.userInfoUrl, {
    headers: {
      authorization: `Bearer ${accessToken}`,
      accept: 'application/json',
    },
  });
  if (!userRes.ok) {
    throw new Error(`OAUTH: profile lookup failed for ${config.provider}`);
  }
  const user = (await userRes.json()) as Record<string, unknown>;
  const email = String(user.email ?? user.preferred_username ?? user.userPrincipalName ?? '');
  const sub = String(user.sub ?? user.oid ?? user.id ?? user.user_id ?? user.userId ?? emailFallback(user, config.provider));
  return {
    email: email || `${config.provider}-${sub}@example.com`,
    displayName: String(user.name ?? user.display_name ?? user.login ?? `${config.provider} user`),
    authSubject: `${config.provider}:${sub}`,
  };
}

function emailFallback(value: Record<string, unknown>, provider: string): string {
  const candidate = String(value.email ?? value.name ?? value.login ?? value.sub ?? '');
  return candidate || `${provider}-user`;
}

export async function completeOAuthCallback(input: {
  provider: string;
  code: string;
  state: string;
  governanceProfile?: GovernanceMode;
}) {
  const provider = normalizeProvider(input.provider);
  if (!provider) {
    throw new Error('OAUTH: unsupported provider');
  }
  const decoded = decodeState(input.state);
  if (!decoded || decoded.provider !== provider) {
    throw new Error('OAUTH: invalid state');
  }
  const config = providerConfig(provider, decoded.redirectUri);
  if (!config) {
    throw new Error(`OAUTH: provider ${provider} is not configured`);
  }

  const tokenResponse = await exchangeCode(config, input.code);
  const profile = await loadProfile(config, tokenResponse);
  const governanceProfile = input.governanceProfile ?? 'balanced';
  const planId = decoded.mode === 'signup' ? 'pro' : 'free';
  const organizationName = decoded.mode === 'signup' ? `${provider} org` : undefined;
  const loginInput: CustomerLoginInput = {
    email: profile.email,
    authProvider: provider,
    authSubject: profile.authSubject,
    governanceProfile,
  };

  try {
    const result = platform.loginCustomer(loginInput);
    return {
      provider,
      mode: decoded.mode as 'login' | 'signup',
      customer: result.customer,
      session: result.session,
      redirectTo: decoded.returnTo || '/pricing',
    };
  } catch (error) {
    if (decoded.mode !== 'signup') {
      throw error;
    }
    const signupInput: CustomerSignupInput = {
      email: profile.email,
      displayName: profile.displayName,
      authProvider: provider,
      authSubject: profile.authSubject,
      planId,
      organizationName,
      organizationRole: 'owner',
      governanceProfile,
    };
    const result = platform.signupCustomer(signupInput);
    return {
      provider,
      mode: decoded.mode as 'login' | 'signup',
      customer: result.customer,
      session: result.session,
      redirectTo: decoded.returnTo || '/pricing',
    };
  }
}
