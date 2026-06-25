import { RuntimeClient } from '../client/RuntimeClient.js';
import type { SpanWire } from '../client/types.js';

export async function listSpans(
  client: RuntimeClient,
  runId: string,
): Promise<SpanWire[]> {
  return client.getSpans(runId);
}

export async function filterSpans(
  client: RuntimeClient,
  runId: string,
  query: { type?: string },
): Promise<SpanWire[]> {
  const spans = await listSpans(client, runId);
  return spans.filter((s) => !query.type || s.type === query.type);
}

export async function timelineSpans(
  client: RuntimeClient,
  runId: string,
): Promise<SpanWire[]> {
  const spans = await listSpans(client, runId);
  return [...spans].sort((a, b) => a.timestamp - b.timestamp);
}
