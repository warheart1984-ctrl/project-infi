export interface ThresholdDelta {
  id: string;
  thresholdId: string;
  fromVersion: number;
  toVersion: number;
  proposedBy: string;
  description: string;
  affectsInvariants: string[];
}
