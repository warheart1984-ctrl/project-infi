type AaisHealthPayload = {
  status?: unknown;
  service?: unknown;
  legacy_api_loaded?: unknown;
  active_model_mode?: unknown;
  ai_status?: unknown;
  ai_bootstrap_status?: unknown;
  mock_mode_active?: unknown;
  contractors?: unknown;
};

export type AaisTelemetryStatus = {
  connected: boolean;
  baseUrl: string;
  statusCode?: number;
  status: string;
  service: string;
  activeModelMode: string;
  aiStatus: string;
  aiBootstrapStatus: string;
  mockModeActive: boolean;
  legacyApiLoaded: boolean;
  contractors: unknown[];
  error?: string;
};

export async function getAaisTelemetryStatus(
  baseUrl = defaultAaisBaseUrl(),
  timeoutMs = 1500,
): Promise<AaisTelemetryStatus> {
  const normalizedBaseUrl = baseUrl.replace(/\/+$/, '');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${normalizedBaseUrl}/health`, { signal: controller.signal });
    const payload = await parseHealthPayload(response);
    return {
      connected: response.ok && String(payload.status ?? '').toLowerCase() === 'healthy',
      baseUrl: normalizedBaseUrl,
      statusCode: response.status,
      status: String(payload.status ?? (response.ok ? 'ok' : 'unhealthy')),
      service: String(payload.service ?? 'AAIS'),
      activeModelMode: String(payload.active_model_mode ?? ''),
      aiStatus: String(payload.ai_status ?? ''),
      aiBootstrapStatus: String(payload.ai_bootstrap_status ?? ''),
      mockModeActive: Boolean(payload.mock_mode_active),
      legacyApiLoaded: Boolean(payload.legacy_api_loaded),
      contractors: Array.isArray(payload.contractors) ? payload.contractors : [],
      ...(response.ok ? {} : { error: `AAIS health returned HTTP ${response.status}` }),
    };
  } catch (error) {
    return {
      connected: false,
      baseUrl: normalizedBaseUrl,
      status: 'unreachable',
      service: 'AAIS',
      activeModelMode: '',
      aiStatus: '',
      aiBootstrapStatus: '',
      mockModeActive: false,
      legacyApiLoaded: false,
      contractors: [],
      error: error instanceof Error ? error.message : String(error),
    };
  } finally {
    clearTimeout(timeout);
  }
}

function defaultAaisBaseUrl(): string {
  return process.env.AAIS_BASE_URL?.trim() || 'http://127.0.0.1:8000';
}

async function parseHealthPayload(response: Response): Promise<AaisHealthPayload> {
  const text = await response.text();
  if (!text.trim()) {
    return {};
  }
  try {
    return JSON.parse(text) as AaisHealthPayload;
  } catch {
    return { status: response.ok ? 'ok' : 'invalid_json' };
  }
}
