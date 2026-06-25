export interface PatchEffectSample {
  patchId: string;
  timestamp: string;
  preRecurrence: number;
  postRecurrence: number;
}

export interface PatchEffectivenessRecord extends PatchEffectSample {
  effectiveness: number;
}

export class PatchAnalytics {
  private readonly records: PatchEffectivenessRecord[] = [];

  recordSample(sample: PatchEffectSample): void {
    const effectiveness =
      sample.preRecurrence === 0
        ? 1
        : Number((1 - sample.postRecurrence / sample.preRecurrence).toFixed(3));
    this.records.push({
      ...sample,
      effectiveness,
    });
  }

  recordEffectiveness(patchId: string, preRecurrence: number, postRecurrence: number): void {
    this.recordSample({
      patchId,
      timestamp: new Date().toISOString(),
      preRecurrence,
      postRecurrence,
    });
  }

  getTimeline(): PatchEffectivenessRecord[] {
    return [...this.records];
  }
}
