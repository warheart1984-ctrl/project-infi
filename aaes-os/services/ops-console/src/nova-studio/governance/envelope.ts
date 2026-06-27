import type { SkillzMcgeeCapability, OperatorContext } from '../state/studioState.js';
import type { GovernanceEnvelope, GovernanceEnvelopeStatus } from './receiptTypes.js';

export function createGovernanceEnvelope(input: {
  operatorContext: OperatorContext;
  capability: SkillzMcgeeCapability;
  input: unknown;
  output?: unknown;
  timestamp?: string;
  status?: GovernanceEnvelopeStatus;
}): GovernanceEnvelope {
  return {
    operator: input.operatorContext.operatorId,
    timestamp: input.timestamp ?? new Date().toISOString(),
    continuityCheckpoint: input.operatorContext.continuity.checkpoint,
    capability: input.capability.name,
    inputHash: deterministicHash(input.input),
    outputHash: input.output === undefined ? undefined : deterministicHash(input.output),
    status: input.status ?? 'pending',
  };
}

export function deterministicHash(value: unknown): string {
  const payload = stableStringify(value);
  let hash = 2166136261;
  for (let index = 0; index < payload.length; index += 1) {
    hash ^= payload.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `fnv1a:${(hash >>> 0).toString(16).padStart(8, '0')}`;
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== 'object') {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableStringify(item)).join(',')}]`;
  }
  const record = value as Record<string, unknown>;
  return `{${Object.keys(record).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(record[key])}`).join(',')}}`;
}
