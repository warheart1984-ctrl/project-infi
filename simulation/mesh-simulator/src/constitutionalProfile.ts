export interface ConstitutionalProfile {
  authority: string;
  evidence: string[];
  replay: string;
  failurePath: string;
}

export const constitutionalProfile: ConstitutionalProfile = {
  authority: 'Governance invariants authorize simulation behavior and message emission.',
  evidence: ['simulation state snapshots', 'agent action streams', 'governance decisions'],
  replay: 'Replay a tick sequence from the captured store state and action log.',
  failurePath: 'Stop the simulation, log the invariant breach, and require governance review.',
};
