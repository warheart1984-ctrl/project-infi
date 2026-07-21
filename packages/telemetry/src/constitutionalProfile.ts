export interface ConstitutionalProfile {
  authority: string;
  evidence: string[];
  replay: string;
  failurePath: string;
}

export const constitutionalProfile: ConstitutionalProfile = {
  authority: 'Telemetry is governed by AAES runtime and governance invariants.',
  evidence: ['metric samples', 'metric snapshots', 'alert thresholds'],
  replay: 'Replay metric samples from the captured in-memory or persisted stream.',
  failurePath: 'Raise a governed alert and annotate the fault journal.',
};
