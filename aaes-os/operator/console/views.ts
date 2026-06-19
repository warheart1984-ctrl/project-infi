/**
 * Read-only operator console views (MVP stubs).
 * Wire to governed-memory façades in a full operator UI.
 */
import type { AuthorityToken, ExecutionSpan, IntentRecord } from "@aaes-os/governed-memory";

export function viewIntent(intent: IntentRecord): string {
  return `Intent ${intent.intent_id} v${intent.version} goal=${intent.goal}`;
}

export function viewAuthority(token: AuthorityToken): string {
  return `Authority ${token.token_id} scopes=${token.scopes.join(",")}`;
}

export function viewSpan(span: ExecutionSpan): string {
  return `Span ${span.span_id} state=${span.state} traces=${span.trace_ids.length}`;
}

export function terminateSpan(span: ExecutionSpan): { terminated: boolean; span_id: string } {
  return { terminated: span.state !== "completed", span_id: span.span_id };
}
