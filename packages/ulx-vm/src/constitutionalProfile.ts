export interface ConstitutionalProfile {
  authority: string;
  evidence: string[];
  replay: string;
  failurePath: string;
}

export const constitutionalProfile: ConstitutionalProfile = {
  authority: 'ULX governance authorizes the VM only after validation and trace capture.',
  evidence: ['VM accept/reject decisions', 'bytecode trace events', 'governance receipts'],
  replay: 'Replay the same bytecode through the validator and VM execution path.',
  failurePath: 'Return a denial result and surface the bytecode for governance review.',
};
