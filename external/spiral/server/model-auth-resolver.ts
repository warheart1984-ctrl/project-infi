import type { ExecutorProviderType, ProviderType } from "@shared/schema";
import {
  getAuthProfileById,
  isOauthProfileExpired,
  type AuthProfileProvider,
} from "./auth-profiles";

export interface ResolveRuntimeAuthInput {
  requestedModel?: string;
  provider: ProviderType;
  authProfileId?: string;
  fallbackInlineApiKey?: string;
  now?: number;
}

export interface ResolveRuntimeAuthResult {
  provider: ProviderType;
  requestedModel?: string;
  source: "inline-api-key";
  headers: Record<string, string>;
}

export interface ResolveExecutorAuthInput {
  provider?: ExecutorProviderType;
  requestedModel?: string;
  authProfileId?: string;
  fallbackInlineApiKey?: string;
  now?: number;
}

export interface ResolveExecutorAuthResult {
  provider: ExecutorProviderType;
  requestedModel?: string;
  profileIdUsed: string;
  source: "auth-profile-oauth";
  accessToken: string;
}

function normalizeString(value: unknown, max = 4000): string | undefined {
  if (typeof value !== "string") return undefined;
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  return trimmed.slice(0, max);
}

function normalizeId(value: unknown): string | undefined {
  const raw = normalizeString(value, 200);
  if (!raw) return undefined;
  const normalized = raw
    .toLowerCase()
    .replace(/[^a-z0-9._-]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80);
  return normalized || undefined;
}

function normalizeExecutorProvider(value: unknown): ExecutorProviderType | undefined {
  return value === "codex-local" ? value : undefined;
}

function buildProviderHeaders(provider: ProviderType, credential: string): Record<string, string> {
  switch (provider) {
    case "openai":
      return {
        Authorization: `Bearer ${credential}`,
      };
    case "azure-openai":
      return {
        "api-key": credential,
      };
    case "anthropic":
      return {
        "x-api-key": credential,
      };
    case "google":
      return {
        "x-goog-api-key": credential,
      };
    default:
      return {};
  }
}

function isExecutorProfileCompatible(profileProvider: AuthProfileProvider): boolean {
  return profileProvider === "openai" || profileProvider === "openai-codex";
}

export async function resolveRuntimeAuth(
  input: ResolveRuntimeAuthInput,
): Promise<ResolveRuntimeAuthResult> {
  const authProfileId = normalizeId(input.authProfileId);
  const inlineApiKey = normalizeString(input.fallbackInlineApiKey);

  if (authProfileId) {
    throw new Error(
      `Runtime provider "${input.provider}" does not accept authProfileId. Use runtime API key credentials.`,
    );
  }

  if (!inlineApiKey) {
    throw new Error(`Runtime provider "${input.provider}" requires fallbackInlineApiKey.`);
  }

  return {
    provider: input.provider,
    ...(input.requestedModel ? { requestedModel: input.requestedModel } : {}),
    source: "inline-api-key",
    headers: buildProviderHeaders(input.provider, inlineApiKey),
  };
}

export async function resolveExecutorAuth(
  input: ResolveExecutorAuthInput,
): Promise<ResolveExecutorAuthResult> {
  const provider = normalizeExecutorProvider(input.provider || "codex-local");
  const authProfileId = normalizeId(input.authProfileId);
  const inlineApiKey = normalizeString(input.fallbackInlineApiKey);
  const now = Math.max(1, Math.floor(input.now || Date.now()));

  if (!provider) {
    throw new Error(`Unsupported executor provider "${input.provider}".`);
  }
  if (inlineApiKey) {
    throw new Error("Executor provider does not accept fallbackInlineApiKey.");
  }
  if (!authProfileId) {
    throw new Error("Executor provider requires authProfileId.");
  }

  const profile = await getAuthProfileById(authProfileId);
  if (!profile) {
    throw new Error(`Auth profile "${authProfileId}" not found.`);
  }
  if (!isExecutorProfileCompatible(profile.provider)) {
    throw new Error(
      `Executor auth profile "${authProfileId}" provider mismatch: profile=${profile.provider}.`,
    );
  }
  if (profile.type !== "oauth") {
    throw new Error(
      `Executor auth profile "${authProfileId}" must be type oauth, received ${profile.type}.`,
    );
  }
  if (isOauthProfileExpired(profile, now)) {
    throw new Error(
      `Auth profile "${profile.id}" OAuth token expired at ${new Date(profile.expiresAt || 0).toISOString()}.`,
    );
  }

  return {
    provider,
    ...(input.requestedModel ? { requestedModel: input.requestedModel } : {}),
    profileIdUsed: profile.id,
    source: "auth-profile-oauth",
    accessToken: profile.accessToken,
  };
}

// Backward-compatible alias for existing call sites while runtime migration is in flight.
export type ResolveModelAuthInput = ResolveRuntimeAuthInput;
export type ResolveModelAuthResult = ResolveRuntimeAuthResult;
export async function resolveModelAuth(
  input: ResolveModelAuthInput,
): Promise<ResolveModelAuthResult> {
  return resolveRuntimeAuth(input);
}
