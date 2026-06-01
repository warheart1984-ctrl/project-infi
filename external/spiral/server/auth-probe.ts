import type { ProviderType, ProviderSettings } from "@shared/schema";
import { getAuthProfileById } from "./auth-profiles";
import { resolveRuntimeAuth } from "./model-auth-resolver";

export type AuthProbeStatus =
  | "ok"
  | "expired"
  | "scope-missing"
  | "provider-mismatch"
  | "invalid"
  | "network-error";

export interface AuthProbeProfileMeta {
  id: string;
  type: "api_key" | "oauth";
  provider: ProviderType | "openai-codex";
  email?: string;
  expiresAt?: number;
}

export interface AuthProbeResult {
  status: AuthProbeStatus;
  statusCode?: number;
  errorCode?: string;
  requiredScopes?: string[];
  message?: string;
  profileMeta?: AuthProbeProfileMeta;
}

interface ProbeHttpResult {
  ok: boolean;
  statusCode: number;
  bodyText: string;
}

function normalize(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function parseRequiredScopes(message: string): string[] {
  const match = message.match(/missing scopes?:\s*([^\n.]+)/i);
  if (!match) return [];
  return match[1]
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function readErrorMessage(raw: string): string {
  const text = normalize(raw);
  if (!text) return "";
  try {
    const parsed = JSON.parse(text) as {
      error?: { message?: unknown } | string;
      message?: unknown;
    };
    if (typeof parsed.error === "string" && normalize(parsed.error)) {
      return normalize(parsed.error);
    }
    if (
      parsed.error &&
      typeof parsed.error === "object" &&
      typeof parsed.error.message === "string" &&
      normalize(parsed.error.message)
    ) {
      return normalize(parsed.error.message);
    }
    if (typeof parsed.message === "string" && normalize(parsed.message)) {
      return normalize(parsed.message);
    }
  } catch {
    // Fall through.
  }
  return text;
}

function classifyResolverError(errorMessage: string): AuthProbeResult {
  const normalized = errorMessage.toLowerCase();
  if (normalized.includes("expired")) {
    return {
      status: "expired",
      errorCode: "auth-profile-expired",
      message: errorMessage,
    };
  }
  if (normalized.includes("provider mismatch")) {
    return {
      status: "provider-mismatch",
      errorCode: "provider-mismatch",
      message: errorMessage,
    };
  }
  if (normalized.includes("not found")) {
    return {
      status: "invalid",
      errorCode: "auth-profile-not-found",
      message: errorMessage,
    };
  }
  return {
    status: "invalid",
    errorCode: "resolver-invalid",
    message: errorMessage || "Credential resolution failed.",
  };
}

function classifyHttpFailure(http: ProbeHttpResult): AuthProbeResult {
  const message = readErrorMessage(http.bodyText);
  const normalized = message.toLowerCase();
  const requiredScopes = parseRequiredScopes(message);
  if (
    (http.statusCode === 401 || http.statusCode === 403) &&
    (normalized.includes("missing scope") ||
      normalized.includes("missing scopes") ||
      normalized.includes("insufficient permissions") ||
      requiredScopes.length > 0)
  ) {
    return {
      status: "scope-missing",
      statusCode: http.statusCode,
      errorCode: "scope-missing",
      ...(requiredScopes.length > 0 ? { requiredScopes } : {}),
      message: message || "Missing required API scope.",
    };
  }
  if (http.statusCode === 401 || http.statusCode === 403) {
    return {
      status: "invalid",
      statusCode: http.statusCode,
      errorCode: "auth-invalid",
      message: message || "Authentication failed.",
    };
  }
  if (http.statusCode === 400 && normalized.includes("model") && normalized.includes("not found")) {
    return {
      status: "invalid",
      statusCode: http.statusCode,
      errorCode: "model-not-found",
      message: message || "Model not found.",
    };
  }
  if (http.statusCode >= 500) {
    return {
      status: "network-error",
      statusCode: http.statusCode,
      errorCode: "provider-server-error",
      message: message || "Provider server error.",
    };
  }
  return {
    status: "invalid",
    statusCode: http.statusCode,
    errorCode: "provider-request-failed",
    message: message || "Provider request failed.",
  };
}

async function sendOpenAIProbe(args: {
  model: string;
  headers: Record<string, string>;
}): Promise<ProbeHttpResult> {
  const response = await fetch(
    "https://api.openai.com/v1/responses",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...args.headers,
      },
      body: JSON.stringify(
        {
          model: args.model,
          input: "ping",
          max_output_tokens: 1,
          stream: false,
        },
      ),
    },
  );
  return {
    ok: response.ok,
    statusCode: response.status,
    bodyText: await response.text(),
  };
}

async function sendAzureProbe(args: {
  endpoint: string;
  deployment: string;
  apiVersion: string;
  headers: Record<string, string>;
}): Promise<ProbeHttpResult> {
  const url = `${args.endpoint.replace(/\/$/, "")}/openai/deployments/${args.deployment}/chat/completions?api-version=${args.apiVersion}`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...args.headers,
    },
    body: JSON.stringify({
      messages: [{ role: "user", content: "ping" }],
      max_tokens: 1,
      stream: false,
    }),
  });
  return {
    ok: response.ok,
    statusCode: response.status,
    bodyText: await response.text(),
  };
}

async function sendAnthropicProbe(args: {
  model: string;
  headers: Record<string, string>;
}): Promise<ProbeHttpResult> {
  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...args.headers,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: args.model,
      max_tokens: 1,
      messages: [{ role: "user", content: "ping" }],
    }),
  });
  return {
    ok: response.ok,
    statusCode: response.status,
    bodyText: await response.text(),
  };
}

async function sendGoogleProbe(args: {
  model: string;
  headers: Record<string, string>;
}): Promise<ProbeHttpResult> {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${args.model}:generateContent`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...args.headers,
    },
    body: JSON.stringify({
      contents: [{ role: "user", parts: [{ text: "ping" }] }],
      generationConfig: { maxOutputTokens: 1 },
    }),
  });
  return {
    ok: response.ok,
    statusCode: response.status,
    bodyText: await response.text(),
  };
}

function resolveProviderDefaultModel(provider: ProviderType): string {
  switch (provider) {
    case "openai":
      return "gpt-4o";
    case "azure-openai":
      return "gpt-4o";
    case "anthropic":
      return "claude-sonnet-4-20250514";
    case "google":
      return "gemini-2.0-flash";
    default:
      return "gpt-4o";
  }
}

export async function probeProviderAuth(settings: ProviderSettings): Promise<AuthProbeResult> {
  const authProfileId = normalize(settings.authProfileId);
  let profileMeta: AuthProbeProfileMeta | undefined;
  if (authProfileId) {
    const profile = await getAuthProfileById(authProfileId);
    if (profile) {
      profileMeta = {
        id: profile.id,
        type: profile.type,
        provider: profile.provider,
        ...(profile.type === "oauth" && profile.email ? { email: profile.email } : {}),
        ...(profile.type === "oauth" && profile.expiresAt ? { expiresAt: profile.expiresAt } : {}),
      };
    }
  }

  let auth:
    | Awaited<ReturnType<typeof resolveRuntimeAuth>>
    | undefined;
  try {
    auth = await resolveRuntimeAuth({
      provider: settings.provider,
      requestedModel: settings.model,
      authProfileId: settings.authProfileId,
      fallbackInlineApiKey: settings.apiKey,
    });
  } catch (error) {
    const classified = classifyResolverError(
      error instanceof Error ? error.message : "Credential resolution failed.",
    );
    return {
      ...classified,
      ...(profileMeta ? { profileMeta } : {}),
    };
  }

  const model = normalize(settings.model) || resolveProviderDefaultModel(settings.provider);

  try {
    let http: ProbeHttpResult;
    switch (settings.provider) {
      case "openai":
        http = await sendOpenAIProbe({
          model,
          headers: auth.headers,
        });
        break;
      case "azure-openai": {
        const endpoint = normalize(settings.endpoint);
        const deployment = normalize(settings.deployment);
        const apiVersion = normalize(settings.apiVersion) || "2024-10-21";
        if (!endpoint || !deployment) {
          return {
            status: "invalid",
            errorCode: "azure-missing-endpoint-or-deployment",
            message: "Azure probe requires endpoint and deployment.",
            ...(profileMeta ? { profileMeta } : {}),
          };
        }
        http = await sendAzureProbe({
          endpoint,
          deployment,
          apiVersion,
          headers: auth.headers,
        });
        break;
      }
      case "anthropic":
        http = await sendAnthropicProbe({
          model,
          headers: auth.headers,
        });
        break;
      case "google":
        http = await sendGoogleProbe({
          model,
          headers: auth.headers,
        });
        break;
      default:
        return {
          status: "invalid",
          errorCode: "unsupported-provider",
          message: `Unsupported provider "${settings.provider}".`,
          ...(profileMeta ? { profileMeta } : {}),
        };
    }

    if (http.ok) {
      return {
        status: "ok",
        statusCode: http.statusCode,
        errorCode: "ok",
        ...(profileMeta ? { profileMeta } : {}),
      };
    }

    return {
      ...classifyHttpFailure(http),
      ...(profileMeta ? { profileMeta } : {}),
    };
  } catch (error) {
    return {
      status: "network-error",
      errorCode: "network-error",
      message: error instanceof Error ? error.message : "Probe failed due to network error.",
      ...(profileMeta ? { profileMeta } : {}),
    };
  }
}
