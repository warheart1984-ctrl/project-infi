import type { Id, ISOTime } from "../css2/types";
import type { ObserverProfile } from "../css2/types";
import type { JudgmentCapability, JudgmentDimension } from "../judgment/capability";
import { JUDGMENT_DIMENSIONS } from "../judgment/capability";
import { computeJudgmentDrift } from "../judgment/drift";
import { judgmentFromObserver } from "../judgment/mapping";
import type { JudgmentCurriculumModuleId } from "./judgment-curriculum";

export interface JudgmentCapabilityLedgerEntry {
  timestamp: ISOTime;
  moduleId?: JudgmentCurriculumModuleId;
  capabilitySnapshot: JudgmentCapability;
  driftScore: number;
}

export interface JudgmentDriftIndicators {
  overall: number;
  byDimension: Partial<Record<JudgmentDimension, number>>;
}

/** JPSS-2.J.3 — capability ledger consumed by CSS-2 and CRK-1. */
export interface JudgmentCapabilityLedger {
  observerId: Id;
  scores: JudgmentCapability;
  driftIndicators: JudgmentDriftIndicators;
  trainingHistory: JudgmentCapabilityLedgerEntry[];
  stewardshipReady: boolean;
  updatedAt: ISOTime;
}

const STEWARDSHIP_READY_THRESHOLD = 0.65;
const STEWARDSHIP_READY_REFLECTION = 0.5;

export function createCapabilityLedger(
  observer: ObserverProfile,
  timestamp: ISOTime = new Date().toISOString(),
): JudgmentCapabilityLedger {
  const scores = judgmentFromObserver(observer);
  return {
    observerId: observer.id,
    scores,
    driftIndicators: { overall: observer.driftScore, byDimension: {} },
    trainingHistory: [
      {
        timestamp,
        capabilitySnapshot: scores,
        driftScore: observer.driftScore,
      },
    ],
    stewardshipReady: assessStewardshipReady(scores, observer.stage),
    updatedAt: timestamp,
  };
}

export function updateCapabilityLedger(
  ledger: JudgmentCapabilityLedger,
  observer: ObserverProfile,
  options: {
    moduleId?: JudgmentCurriculumModuleId;
    timestamp?: ISOTime;
  } = {},
): JudgmentCapabilityLedger {
  const timestamp = options.timestamp ?? new Date().toISOString();
  const previous = ledger.scores;
  const scores = judgmentFromObserver(observer);
  const overallDrift = computeJudgmentDrift(previous, scores);

  const byDimension: Partial<Record<JudgmentDimension, number>> = {};
  for (const dim of JUDGMENT_DIMENSIONS) {
    byDimension[dim] = Math.abs(previous[dim] - scores[dim]);
  }

  const entry: JudgmentCapabilityLedgerEntry = {
    timestamp,
    moduleId: options.moduleId,
    capabilitySnapshot: scores,
    driftScore: overallDrift,
  };

  return {
    observerId: observer.id,
    scores,
    driftIndicators: {
      overall: Math.max(ledger.driftIndicators.overall, overallDrift),
      byDimension,
    },
    trainingHistory: [...ledger.trainingHistory, entry],
    stewardshipReady: assessStewardshipReady(scores, observer.stage),
    updatedAt: timestamp,
  };
}

function assessStewardshipReady(
  scores: JudgmentCapability,
  stage: ObserverProfile["stage"],
): boolean {
  if (stage !== "steward" && stage !== "senior_observer") return false;
  const avg =
    JUDGMENT_DIMENSIONS.reduce((s, d) => s + scores[d], 0) / JUDGMENT_DIMENSIONS.length;
  return avg >= STEWARDSHIP_READY_THRESHOLD && scores.reflection >= STEWARDSHIP_READY_REFLECTION;
}

export class InMemoryCapabilityLedgerStore {
  private ledgers = new Map<Id, JudgmentCapabilityLedger>();

  get(observerId: Id): JudgmentCapabilityLedger | undefined {
    return this.ledgers.get(observerId);
  }

  upsert(ledger: JudgmentCapabilityLedger): void {
    this.ledgers.set(ledger.observerId, ledger);
  }

  list(): JudgmentCapabilityLedger[] {
    return [...this.ledgers.values()];
  }
}
