import type { GovernedReceipt } from "../governance/receipts";
import type { LineageRecord } from "../governance/lineage";

export type GovernedMode = "predict" | "observe" | "correct";

export interface GovernedContext {
  operator_id: string;
  mode: GovernedMode;
  invariant_set_version: string;
  model_path?: string;
}

export interface CE1Record {
  id: string;
  calibration_event: string;
  timestamp: number;
}

export interface CRR1Record {
  id: string;
  reconstruction_hash: string;
  timestamp: number;
}

export interface CLG1Record {
  id: string;
  parent_id: string | null;
  append_hash: string;
  timestamp: number;
}

export interface GovernedResult {
  output: string;
  receipt: GovernedReceipt;
  lineage: LineageRecord;
  ce1: CE1Record;
  crr1: CRR1Record;
  clg1: CLG1Record;
}
