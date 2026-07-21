export interface ConstitutionalProfile {
  authority: string;
  evidence: string[];
  replay: string;
  failurePath: string;
}

export const constitutionalProfile: ConstitutionalProfile = {
  authority: 'Nova Shell is governed by AAES runtime approvals and constitutional freeze.',
  evidence: ['mission state', 'runtime approvals', 'ledgered decisions'],
  replay: 'Replay Nova missions from the mission engine state and ledgered approvals.',
  failurePath: 'Halt the shell workflow and surface the denial to the operator.',
};
