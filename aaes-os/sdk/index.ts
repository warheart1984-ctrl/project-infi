export * as cas from './cas/index.js';
export * as governance from './governance/index.js';
export * as cdp1 from './cdp1/minimal.js';
export * as util from './util/hash.js';
export { equal, deepEqual } from './util/assert.js';
export { hashReceipt } from './util/hash.js';
export { RuntimeClient } from './client/RuntimeClient.js';
export type {
  RuntimeConfig,
  Identity,
  ExecuteRequest,
  ExecuteResponse,
  SpanWire,
  ReceiptWire,
  FaultWire,
} from './client/types.js';
export { createLocalSdk } from './local/createLocalSdk.js';
export type { LocalSdk } from './local/createLocalSdk.js';

/** @deprecated Use createLocalSdk */
export { createLocalSdk as createSdk } from './local/createLocalSdk.js';
/** @deprecated Use LocalSdk */
export type { LocalSdk as AaesSdk } from './local/createLocalSdk.js';
