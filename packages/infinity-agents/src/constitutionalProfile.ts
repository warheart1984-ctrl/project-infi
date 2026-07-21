export interface ConstitutionalProfile {
  authority: string;
  evidence: string[];
  replay: string;
  failurePath: string;
}

export const constitutionalProfile: ConstitutionalProfile = {
  authority: 'Infinity Agents execute only within AAES governance, sandbox, and capability boundaries.',
  evidence: ['agent actions', 'scheduler traces', 'sandbox decisions'],
  replay: 'Replay orchestration tasks and agent responses from the ledgered action stream.',
  failurePath: 'Quarantine the agent, log the fault, and halt orchestration if needed.',
};
