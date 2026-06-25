export type NexusExecutionEvent = {
  recorded_at?: string;
  mission_id?: string;
  law_eval_id?: string;
  aaes_trace_id?: string;
  aaes_status?: string;
  steward_id?: string;
  darz_bridge_hash?: string;
  blocked?: boolean;
  event_type?: string;
};

export async function getNexusExecutionEvents(
  baseUrl = defaultAaisBaseUrl(),
  timeoutMs = 1500,
): Promise<{ executions: NexusExecutionEvent[]; error?: string }> {
  const normalizedBaseUrl = baseUrl.replace(/\/+$/, '');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${normalizedBaseUrl}/api/nexus/executions`, {
      signal: controller.signal,
    });
    const payload = (await response.json()) as { executions?: NexusExecutionEvent[] };
    return {
      executions: Array.isArray(payload.executions) ? payload.executions : [],
      ...(response.ok ? {} : { error: `Nexus executions returned HTTP ${response.status}` }),
    };
  } catch (error) {
    return {
      executions: [],
      error: error instanceof Error ? error.message : String(error),
    };
  } finally {
    clearTimeout(timeout);
  }
}

function defaultAaisBaseUrl(): string {
  return process.env.AAIS_BASE_URL?.trim() || 'http://127.0.0.1:8000';
}
