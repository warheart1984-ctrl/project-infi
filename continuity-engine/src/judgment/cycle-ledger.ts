import type { Id, ISOTime } from "../css2/types";
import {
  annotateCorrigibility,
  assessCorrigibility,
  type CorrigibilityAssessment,
  type CorrigibilityStatus,
  type JudgmentCycle,
} from "./cycle";

export interface JudgmentCycleLedgerEntry {
  cycle: JudgmentCycle;
  corrigibility: CorrigibilityAssessment;
  recordedAt: ISOTime;
}

/** Per-observer judgment cycle ledger with lineage-level corrigibility rollup. */
export interface JudgmentCycleLedger {
  observerId: Id;
  cycles: JudgmentCycleLedgerEntry[];
  lineageCorrigibility: CorrigibilityStatus;
  updatedAt: ISOTime;
}

const STATUS_RANK: Record<CorrigibilityStatus, number> = {
  sound: 0,
  "at-risk": 1,
  failed: 2,
};

export function rollupLineageCorrigibility(
  statuses: CorrigibilityStatus[],
): CorrigibilityStatus {
  if (statuses.length === 0) return "at-risk";
  let worst: CorrigibilityStatus = "sound";
  for (const status of statuses) {
    if (STATUS_RANK[status] > STATUS_RANK[worst]) {
      worst = status;
    }
  }
  return worst;
}

export function createJudgmentCycleLedger(
  observerId: Id,
  timestamp: ISOTime = new Date().toISOString(),
): JudgmentCycleLedger {
  return {
    observerId,
    cycles: [],
    lineageCorrigibility: "at-risk",
    updatedAt: timestamp,
  };
}

export function recordJudgmentCycle(
  ledger: JudgmentCycleLedger,
  cycle: JudgmentCycle,
  timestamp: ISOTime = new Date().toISOString(),
): JudgmentCycleLedger {
  const corrigibility = assessCorrigibility(cycle);
  const annotated = annotateCorrigibility(cycle);
  const entry: JudgmentCycleLedgerEntry = {
    cycle: annotated,
    corrigibility,
    recordedAt: timestamp,
  };
  const cycles = [...ledger.cycles, entry];
  return {
    observerId: ledger.observerId,
    cycles,
    lineageCorrigibility: rollupLineageCorrigibility(
      cycles.map((e) => e.corrigibility.status),
    ),
    updatedAt: timestamp,
  };
}

export class InMemoryJudgmentCycleLedgerStore {
  private ledgers = new Map<Id, JudgmentCycleLedger>();

  get(observerId: Id): JudgmentCycleLedger | undefined {
    return this.ledgers.get(observerId);
  }

  record(cycle: JudgmentCycle, timestamp?: ISOTime): JudgmentCycleLedger {
    const existing =
      this.ledgers.get(cycle.observerId) ??
      createJudgmentCycleLedger(cycle.observerId, timestamp);
    const updated = recordJudgmentCycle(existing, cycle, timestamp);
    this.ledgers.set(cycle.observerId, updated);
    return updated;
  }

  list(): JudgmentCycleLedger[] {
    return [...this.ledgers.values()];
  }
}
