export interface ConstitutionalProfile {
  authority: string;
  evidence: string[];
  replay: string;
  failurePath: string;
}

export const constitutionalProfile: ConstitutionalProfile = {
  authority: 'AAIS runs as a simple llm -> jarvis -> nova governed path under AAES invariants.',
  evidence: ['LLM normalization output', 'Jarvis doctrine and invariant results', 'Nova bus dispatch records'],
  replay: 'Rehydrate the ordered AAIS flow from the ledger and replay the llm, jarvis, and nova stages.',
  failurePath: 'Stop at Jarvis, emit the validation reason, and keep Nova from dispatching.',
};
