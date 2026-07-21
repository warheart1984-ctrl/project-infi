import { createHash } from 'node:crypto';

import type { EvidenceBundle, StepResult } from './types.js';

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

export class EvidenceBundleCollector {
  collect(stepResult: StepResult): EvidenceBundle {
    return {
      bundle_id: `eb_${Date.now()}`,
      step_index: stepResult.stepIndex,
      actor_id: stepResult.actorId,
      action: stepResult.action,
      output_hash: sha256(stepResult.output),
      evidence_refs: [stepResult.trace_id],
      collected_at: new Date().toISOString(),
    };
  }
}

export { sha256 };
