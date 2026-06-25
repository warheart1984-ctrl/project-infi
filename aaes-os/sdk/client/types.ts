/**
 * Wire types derived from OpenAPI — regenerate via `pnpm sdk:generate`.
 */
import type { components } from '../generated/types.js';

export type RuntimeConfig = {
  baseUrl: string;
  apiKey?: string;
};

export type Identity = components['schemas']['Identity'];
export type ExecuteRequest = components['schemas']['ExecuteRequest'];
export type ExecuteResponse = components['schemas']['ExecuteResponse'];
export type SpanWire = components['schemas']['Span'];
export type ReceiptWire = components['schemas']['Receipt'];
export type FaultWire = components['schemas']['Fault'];
export type InvariantInfo = components['schemas']['InvariantInfo'];

export type { components, paths, operations } from '../generated/types.js';
