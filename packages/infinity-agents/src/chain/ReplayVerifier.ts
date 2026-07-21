import type { EvidenceBundle, ReplayReport, StepResult } from './types.js';
import { sha256 } from './EvidenceBundleCollector.js';

export class ReplayVerifier {
  verify(bundle: EvidenceBundle, stepResult: StepResult): ReplayReport {
    const replay_hash = sha256(stepResult.output);
    const matches = replay_hash === bundle.output_hash;

    return {
      report_id: `rr_${Date.now()}`,
      bundle_id: bundle.bundle_id,
      replay_hash,
      original_hash: bundle.output_hash,
      matches,
      verified_at: new Date().toISOString(),
    };
  }
}
