import routingMap from '../routing/map.json';

export type ChatMode = 'normal' | 'think' | 'research';

export type ChatContext = {
  session_id?: string;
  system_prompt?: string;
  persona_mode?: string;
  provider?: string;
  provider_mode?: string;
  requested_specialists?: string[];
  requested_specialist_preset?: string | null;
};

export type ChatRequest = {
  input: string;
  context?: ChatContext;
  mode?: ChatMode;
  signal?: AbortSignal;
};

export type ChatResponse = {
  output: string;
  trace: Record<string, unknown> | null;
  status: 'ok' | 'degraded' | 'blocked';
  session_id: string;
  runtime: Record<string, unknown>;
};

export type MemoryWriteRequest = {
  text: string;
  tags?: string[];
  source?: string;
  category?: string;
  kind?: string;
  why?: string;
  signal?: AbortSignal;
};

type RouteName = keyof typeof routingMap.routes;

function trimTrailingSlash(value: string): string {
  return String(value || '').trim().replace(/\/+$/, '');
}

function isLocalHost(hostname: string): boolean {
  return hostname === '127.0.0.1' || hostname === 'localhost';
}

export function resolveIntegrationBaseUrl(baseUrl?: string): string {
  if (baseUrl) {
    return trimTrailingSlash(baseUrl);
  }

  if (typeof import.meta !== 'undefined') {
    const env = (import.meta as ImportMeta & {
      env?: Record<string, string | undefined>;
    }).env ?? {};
    const configured = env.VITE_API_URL || env.REACT_APP_API_URL;
    if (configured) {
      return trimTrailingSlash(configured);
    }
  }

  if (typeof window !== 'undefined') {
    if (isLocalHost(window.location.hostname)) {
      return trimTrailingSlash(routingMap.defaults.base_url);
    }
    return trimTrailingSlash(window.location.origin);
  }

  return trimTrailingSlash(routingMap.defaults.base_url);
}

export function resolveIntegrationRoute(
  routeName: RouteName,
  params: Record<string, string> = {},
  baseUrl?: string,
): string {
  const template = routingMap.routes[routeName];
  const path = Object.entries(params).reduce(
    (current, [key, value]) => current.replace(`{${key}}`, encodeURIComponent(String(value))),
    template,
  );
  return `${resolveIntegrationBaseUrl(baseUrl)}${path}`;
}

function buildSessionPayload(context: ChatContext = {}): Record<string, unknown> {
  return {
    system_prompt: context.system_prompt,
    persona_mode: context.persona_mode,
    provider: context.provider,
    provider_mode: context.provider_mode,
    requested_specialists: context.requested_specialists,
    requested_specialist_preset: context.requested_specialist_preset,
  };
}

function buildMessagePayload(request: ChatRequest): Record<string, unknown> {
  const context = request.context || {};
  return {
    message: request.input,
    persona_mode: context.persona_mode,
    provider: context.provider,
    provider_mode: context.provider_mode,
    requested_specialists: context.requested_specialists,
    requested_specialist_preset: context.requested_specialist_preset,
    response_mode: request.mode === 'think' ? 'think' : undefined,
    use_research: request.mode === 'research',
  };
}

function inferResponseStatus(payload: Record<string, unknown>, responseOk: boolean): 'ok' | 'degraded' | 'blocked' {
  if (!responseOk || payload.error) {
    return 'blocked';
  }

  const trace = (payload.response_trace || {}) as Record<string, unknown>;
  const outputCompletion = (trace.output_completion || {}) as Record<string, unknown>;
  const providerDispatch = (trace.provider_dispatch || {}) as Record<string, unknown>;

  if (
    payload.provider_notice
    || outputCompletion.truncation_detected
    || outputCompletion.repetition_detected
    || outputCompletion.completion_guard_applied
    || providerDispatch.prompt_overflow_tokens
  ) {
    return 'degraded';
  }

  return 'ok';
}

async function parseJson(response: Response): Promise<Record<string, unknown>> {
  try {
    return (await response.json()) as Record<string, unknown>;
  } catch {
    return {};
  }
}

export async function createJarvisSession(
  context: ChatContext = {},
  baseUrl?: string,
): Promise<Record<string, unknown>> {
  const response = await fetch(resolveIntegrationRoute('jarvis_sessions', {}, baseUrl), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(buildSessionPayload(context)),
  });

  const payload = await parseJson(response);
  if (!response.ok) {
    throw new Error(String(payload.error || 'Unable to create Jarvis session'));
  }
  return payload;
}

export async function sendToJarvis(
  request: ChatRequest,
  baseUrl?: string,
): Promise<ChatResponse> {
  const response = await fetch(resolveIntegrationRoute('jarvis_chat', {}, baseUrl), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      input: request.input,
      context: request.context || {},
      mode: request.mode || 'normal',
    }),
    signal: request.signal,
  });

  const payload = await parseJson(response);
  const status = String(payload.status || inferResponseStatus(payload, response.ok)) as ChatResponse['status'];

  if (!response.ok) {
    throw new Error(String(payload.error || 'Jarvis request failed'));
  }

  return {
    output: String(payload.output || ''),
    trace: (payload.trace || null) as Record<string, unknown> | null,
    status,
    session_id: String(payload.session_id || ''),
    runtime: (payload.runtime || payload) as Record<string, unknown>,
  };
}

export async function writeJarvisMemory(
  request: MemoryWriteRequest,
  baseUrl?: string,
): Promise<Record<string, unknown>> {
  const response = await fetch(resolveIntegrationRoute('memory_write', {}, baseUrl), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: request.text,
      tags: request.tags,
      source: request.source,
      category: request.category,
      kind: request.kind,
      why: request.why,
    }),
    signal: request.signal,
  });

  const payload = await parseJson(response);
  if (!response.ok) {
    throw new Error(String(payload.error || 'Jarvis memory write failed'));
  }
  return payload;
}

export async function getSystemHealth(baseUrl?: string): Promise<Record<string, unknown>> {
  const response = await fetch(resolveIntegrationRoute('health', {}, baseUrl), {
    method: 'GET',
  });

  const payload = await parseJson(response);
  if (!response.ok) {
    throw new Error(String(payload.error || 'Health check failed'));
  }
  return payload;
}

export const systemRoutingMap = routingMap;
