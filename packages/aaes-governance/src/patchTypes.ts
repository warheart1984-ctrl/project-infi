export interface PatchEffectSample {
  patchId: string;
  timestamp: string;
  preRecurrence: number;
  postRecurrence: number;
}

export interface PatchEffectivenessPoint {
  patchId: string;
  timestamp: string;
  /** 0–1; 1 = eliminated recurrence */
  effectiveness: number;
}
