import { asInvariantId, asRunId, asSpanId } from '@aaes-os/runledger';

import type { FaultJournal, PatchAnalytics, PatternLedger } from '@aaes-os/aaes-governance';

const FAULT_OUTPUT_SHAPE = 'INV_FAIL_INV_OUTPUT_SHAPE';
const FAULT_DETERMINISM = 'INV_FAIL_INV_DETERMINISM';

/** Injects demo faults and patch samples for the Ops Console. */
export function seedTelemetry(
  journal: FaultJournal,
  patterns: PatternLedger,
  patchAnalytics: PatchAnalytics,
): void {
  for (let i = 0; i < 12; i += 1) {
    const fault = journal.recordFault({
      runId: asRunId(`run-seed-shape-${i}`),
      spanId: asSpanId(`span-seed-shape-${i}`),
      invariantId: asInvariantId('INV_OUTPUT_SHAPE'),
      faultCode: FAULT_OUTPUT_SHAPE,
      severity: 'ERROR',
      contextSnapshot: { seeded: true, kind: 'output_shape', index: i },
    });
    patterns.ingestFault(fault);
  }

  for (let i = 0; i < 8; i += 1) {
    const fault = journal.recordFault({
      runId: asRunId(`run-seed-det-${i}`),
      spanId: asSpanId(`span-seed-det-${i}`),
      invariantId: asInvariantId('INV_DETERMINISM'),
      faultCode: FAULT_DETERMINISM,
      severity: 'ERROR',
      contextSnapshot: { seeded: true, kind: 'determinism', index: i },
    });
    patterns.ingestFault(fault);
  }

  patchAnalytics.recordSample({
    patchId: 'PATCH_OUTPUT_SHAPE_001',
    timestamp: new Date().toISOString(),
    preRecurrence: 12,
    postRecurrence: 3,
  });

  patchAnalytics.recordSample({
    patchId: 'PATCH_DETERMINISM_001',
    timestamp: new Date().toISOString(),
    preRecurrence: 8,
    postRecurrence: 2,
  });
}
