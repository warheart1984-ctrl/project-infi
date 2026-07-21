import type { Invariant } from '@aaes-os/aaes-governance';

function readRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

export const ULXTraceInvariant: Invariant = {
  id: 'I-ULX-001',
  description: 'ULX execution must be traced before runtime commit',
  check(context) {
    const payload = readRecord(context.payload);
    const tracePresent = payload.traceVerified === true || payload.traced === true || payload.traceId !== undefined;

    return {
      passed: tracePresent,
      severity: tracePresent ? 'info' : 'fatal',
      invariantId: 'I-ULX-001',
      message: tracePresent ? 'ULX trace verified' : 'ULX execution is missing a trace',
    };
  },
};
