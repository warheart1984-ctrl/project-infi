export interface Envelope {
  proposalHash: string;
  proposal: any; // In practice, this would be a specific Proposal type
  ucrDecision: { ok: boolean; reasons: string[] };
  alaPlan: { normalized: any[] };
  safetyDecision: { ok: boolean; violations: string[] };
  applied: { applied: any[] };
  timestamp: string;
}
