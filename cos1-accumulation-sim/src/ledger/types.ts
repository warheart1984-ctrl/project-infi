import type { JudgmentCycle } from "../judgment/types.js";

export interface ThresholdView {
  id: string;
  domain: string;
  metric: string;
  comparator: string;
  value: number;
  supportingCycleIds: string[];
  lastUpdatedAt: string;
  createdByObserverId: string;
}

export interface RecalibrationView {
  id: string;
  thresholdId: string;
  fromValue: number;
  toValue: number;
  cycleId: string;
  createdAt: string;
  createdByObserverId: string;
}

export interface ContinuityLedger {
  appendCycle(cycle: JudgmentCycle): Promise<void>;
  getCycle(id: string): Promise<JudgmentCycle | null>;
  getCyclesByObserver(observerId: string): Promise<JudgmentCycle[]>;
  getAllCycles(): Promise<JudgmentCycle[]>;
  getThresholdViews(): Promise<ThresholdView[]>;
  getRecalibrationViews(thresholdId: string): Promise<RecalibrationView[]>;
}
