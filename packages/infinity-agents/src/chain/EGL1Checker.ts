import type { EGL1Report, EvidenceBundle, StepResult } from './types.js';

export class EGL1Checker {
  evaluate(stepResult: StepResult, bundle: EvidenceBundle): EGL1Report {
    const classes = {
      behavioral: this.checkBehavioral(stepResult),
      drift: this.checkDrift(stepResult),
      failureMode: this.checkFailureMode(stepResult),
      evidencePath: this.checkEvidencePath(bundle),
      constitutional: this.checkConstitutional(stepResult),
    };
    const passed = Object.values(classes).every(Boolean);

    return {
      report_id: `egl1_${Date.now()}`,
      bundle_id: bundle.bundle_id,
      classes,
      passed,
      evaluated_at: new Date().toISOString(),
    };
  }

  private checkDrift(stepResult: StepResult): boolean {
    return (stepResult.drift ?? 0) <= 0.036;
  }

  private checkBehavioral(stepResult: StepResult): boolean {
    return !!stepResult.output;
  }

  private checkFailureMode(stepResult: StepResult): boolean {
    return stepResult.error === undefined;
  }

  private checkEvidencePath(bundle: EvidenceBundle): boolean {
    return bundle.evidence_refs.length > 0;
  }

  private checkConstitutional(stepResult: StepResult): boolean {
    return !!stepResult.trace_id;
  }
}
