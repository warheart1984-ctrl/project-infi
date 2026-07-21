import type { ConformanceReport, EGL1Report, ReplayReport } from './types.js';

export class ConformanceGate {
  check(egl1Report: EGL1Report, replayReport: ReplayReport): ConformanceReport {
    const admitted = egl1Report.passed && replayReport.matches;

    if (!admitted) {
      throw new Error(
        `CONFORMANCE GATE: step blocked — EGL1 passed: ${egl1Report.passed}, replay matches: ${replayReport.matches}`,
      );
    }

    return {
      report_id: `conf_${Date.now()}`,
      egl1_report_id: egl1Report.report_id,
      replay_report_id: replayReport.report_id,
      admitted,
      certified_at: new Date().toISOString(),
    };
  }
}
