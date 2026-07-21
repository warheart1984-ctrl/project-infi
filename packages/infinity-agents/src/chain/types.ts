export interface PlanStep {
  command: string;
}

export interface StepResult {
  stepIndex: number;
  actorId: string;
  action: string;
  output: unknown;
  trace_id: string;
  drift?: number;
  error?: string;
  bundle?: EvidenceBundle;
  replayReport?: ReplayReport;
  egl1Report?: EGL1Report;
  conformanceReport?: ConformanceReport;
}

export interface EvidenceBundle {
  bundle_id: string;
  step_index: number;
  actor_id: string;
  action: string;
  output_hash: string;
  evidence_refs: string[];
  collected_at: string;
}

export interface ReplayReport {
  report_id: string;
  bundle_id: string;
  replay_hash: string;
  original_hash: string;
  matches: boolean;
  verified_at: string;
}

export interface EGL1Report {
  report_id: string;
  bundle_id: string;
  classes: {
    behavioral: boolean;
    drift: boolean;
    failureMode: boolean;
    evidencePath: boolean;
    constitutional: boolean;
  };
  passed: boolean;
  evaluated_at: string;
}

export interface ConformanceReport {
  report_id: string;
  egl1_report_id: string;
  replay_report_id: string;
  admitted: boolean;
  certified_at: string;
}
