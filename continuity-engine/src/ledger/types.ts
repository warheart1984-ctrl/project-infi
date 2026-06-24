/** Continuity Ledger v2 — canonical artifact types. */

export type {
  CorrigibilityStatus,
  JudgmentCycle,
  CorrigibilityAssessment,
} from "../judgment/cycle";

export { assessCorrigibility, annotateCorrigibility, isCorrigibilitySound } from "../judgment/cycle";

export type { RealityVetoReceipt, RealityVetoSeverity } from "../rpa1/reality-veto";

export interface ThresholdView {
  thresholdId: string;
  cycleCount: number;
  lastCorrigibility: import("../judgment/cycle").CorrigibilityStatus;
  relatedVetoCount: number;
  observerIds: string[];
}

export interface RecalibrationView {
  thresholdId: string;
  deltaIds: string[];
  cycles: import("../judgment/cycle").JudgmentCycle[];
  corrigibility: import("../judgment/cycle").CorrigibilityStatus;
}

export type ContinuityHealth = "healthy" | "at-risk" | "collapsed";

export type ConstitutionalFailureMode = "F-1" | "F-2" | "F-3";

export interface ContinuityHealthReport {
  health: ContinuityHealth;
  failureModes: ConstitutionalFailureMode[];
  lineageCorrigibility: import("../judgment/cycle").CorrigibilityStatus;
  soundLineageCount: number;
  failedLineageCount: number;
  pendingVetoCount: number;
}
