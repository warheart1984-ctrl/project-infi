import type { ContinuityLedger } from "../ledger/continuity-ledger";
import { assessCorrigibility, type JudgmentCycle } from "../judgment/cycle";
import {
  buildMandatoryReconsiderationCycle,
  type RealityVetoReceipt,
} from "../rpa1/reality-veto";

export interface Expectation {
  id: string;
  description: string;
  predictedOutcome: unknown;
}

export interface ObservedEvent {
  id: string;
  outcome: unknown;
  evidence: unknown;
}

export interface GovernanceDecision {
  allowed: boolean;
  reasons: string[];
  realityVeto?: RealityVetoReceipt;
}

/** Detect when observed outcome violates a steward expectation beyond tolerance. */
export function detectRealityVeto(
  expectation: Expectation,
  observed: ObservedEvent,
  tolerance: (pred: unknown, actual: unknown) => boolean,
  options: { observerId?: string; severity?: RealityVetoReceipt["severity"] } = {},
): RealityVetoReceipt | null {
  const ok = tolerance(expectation.predictedOutcome, observed.outcome);
  if (ok) return null;

  return {
    id: `rv_${observed.id}`,
    timestamp: new Date().toISOString(),
    observerId: options.observerId,
    violatedExpectation: expectation,
    observedOutcome: observed.outcome,
    evidence: observed.evidence,
    severity: options.severity ?? "major",
  };
}

/** Append veto to ledger and enqueue mandatory reconsideration cycle. */
export async function processRealityVeto(
  ledger: ContinuityLedger,
  veto: RealityVetoReceipt,
): Promise<JudgmentCycle> {
  await ledger.appendRealityVeto(veto);
  const reconsideration = buildMandatoryReconsiderationCycle(veto);
  await ledger.appendCycle(reconsideration);
  return reconsideration;
}

/** RPA-1 / CRK-1.J structural gate — non-corrigible cycles cannot proceed. */
export function applyGovernanceWithRealityVeto(
  cycle: JudgmentCycle,
  baseDecision: GovernanceDecision,
): GovernanceDecision {
  const { status } = assessCorrigibility(cycle);

  if (status === "failed") {
    return {
      allowed: false,
      reasons: [
        ...baseDecision.reasons,
        "CRK-1.J / RPA-1: judgment cycle is non-corrigible; reality cannot correct this decision",
      ],
    };
  }

  return baseDecision;
}
