import type { Id, ISOTime } from "../css2/types";
import type { JudgmentCycle } from "../judgment/cycle";
import { annotateCorrigibility } from "../judgment/cycle";

export type RealityVetoSeverity = "minor" | "major" | "critical";

/** RV-2 — Veto Receipt stored in the Continuity Ledger. */
export interface RealityVetoReceipt {
  id: Id;
  timestamp: ISOTime;
  observerId?: Id;
  violatedExpectation: unknown;
  observedOutcome: unknown;
  evidence: unknown;
  severity: RealityVetoSeverity;
  /** Steward attempted to suppress — triggers RV-4 escalation. */
  suppressed?: boolean;
}

export interface EvidenceMonitorInput {
  expected: unknown;
  observed: unknown;
  evidence: unknown;
  observerId?: Id;
  /** Numeric tolerance (absolute). Default 0 for exact match on numbers. */
  tolerance?: number;
  timestamp?: ISOTime;
}

export interface RealityVetoConfig {
  minorThreshold: number;
  majorThreshold: number;
  criticalThreshold: number;
}

export const DEFAULT_REALITY_VETO_CONFIG: RealityVetoConfig = {
  minorThreshold: 0.05,
  majorThreshold: 0.2,
  criticalThreshold: 0.5,
};

/** RV-1 — Evidence Monitor: divergence exceeds constitutional tolerance. */
export function detectRealityDivergence(
  input: EvidenceMonitorInput,
  config: RealityVetoConfig = DEFAULT_REALITY_VETO_CONFIG,
): boolean {
  const magnitude = computeDivergenceMagnitude(input.expected, input.observed, input.tolerance);
  return magnitude >= config.minorThreshold;
}

export function computeDivergenceMagnitude(
  expected: unknown,
  observed: unknown,
  tolerance = 0,
): number {
  if (expected === observed) return 0;
  if (typeof expected === "number" && typeof observed === "number") {
    const denom = Math.max(Math.abs(expected), 1);
    return Math.abs(observed - expected) / denom;
  }
  if (typeof expected === "string" && typeof observed === "string") {
    return expected === observed ? 0 : 1;
  }
  if (expected == null || observed == null) return 1;
  try {
    return JSON.stringify(expected) === JSON.stringify(observed) ? 0 : 1;
  } catch {
    return 1;
  }
}

export function classifyVetoSeverity(
  magnitude: number,
  config: RealityVetoConfig = DEFAULT_REALITY_VETO_CONFIG,
): RealityVetoSeverity {
  if (magnitude >= config.criticalThreshold) return "critical";
  if (magnitude >= config.majorThreshold) return "major";
  return "minor";
}

/** RV-1 + RV-2 — issue a non-optional Reality Veto when evidence contradicts expectation. */
export function issueRealityVeto(
  input: EvidenceMonitorInput,
  config: RealityVetoConfig = DEFAULT_REALITY_VETO_CONFIG,
): RealityVetoReceipt | null {
  const magnitude = computeDivergenceMagnitude(
    input.expected,
    input.observed,
    input.tolerance,
  );
  if (magnitude < config.minorThreshold) return null;

  const timestamp = input.timestamp ?? new Date().toISOString();
  return {
    id: `rv-${timestamp}-${Math.random().toString(36).slice(2, 9)}`,
    timestamp,
    observerId: input.observerId,
    violatedExpectation: input.expected,
    observedOutcome: input.observed,
    evidence: input.evidence,
    severity: classifyVetoSeverity(magnitude, config),
  };
}

/** RV-3 — Mandatory Reconsideration Cycle from veto evidence. */
export function buildMandatoryReconsiderationCycle(
  receipt: RealityVetoReceipt,
): JudgmentCycle {
  const cycle: JudgmentCycle = {
    id: `jc-veto-${receipt.id}`,
    observerId: receipt.observerId ?? "system:reality-veto",
    timestamp: receipt.timestamp,
    observation: receipt.evidence,
    interpretation: {
      framing: "contradiction_analysis",
      alternatives: [
        { label: "expectation_wrong", description: "Prior expectation does not match reality" },
        { label: "measurement_error", description: "Observation or expectation measurement flawed" },
        { label: "context_shift", description: "Environmental context changed since expectation formed" },
      ],
      violatedExpectation: receipt.violatedExpectation,
      observedOutcome: receipt.observedOutcome,
    },
    valuation: {
      whatMatters: "risk_of_ignoring_reality",
      severity: receipt.severity,
      rationale: "Reality Veto — evidence contradicts internal judgment",
    },
    decision: {
      actorId: receipt.observerId ?? "system:reality-veto",
      action: "proposed_correction",
      vetoId: receipt.id,
    },
    context: { source: "RPA-1", mandatory: true, skippable: false },
    outcome: { metrics: { vetoSeverity: receipt.severity, pending: true } },
    feedback: receipt.evidence,
    reflection: {
      changes: ["mandatory_reconsideration"],
      stewardAccountability: true,
    },
    tags: ["reality-veto", "mandatory-reconsideration"],
  };
  return annotateCorrigibility(cycle);
}

export interface VetoEscalationResult {
  judgmentIllegitimate: boolean;
  blockThresholdChanges: boolean;
  stewardLineageAtRisk: boolean;
  lineageCorrigibilityFailed: boolean;
  reasons: string[];
}

/** RV-4 — Governance escalation when steward ignores or suppresses a veto. */
export function escalateIgnoredVeto(
  receipt: RealityVetoReceipt,
  options: { ignored?: boolean; suppressed?: boolean } = {},
): VetoEscalationResult {
  const ignored = options.ignored ?? false;
  const suppressed = options.suppressed ?? receipt.suppressed ?? false;
  const reasons: string[] = [];

  if (!ignored && !suppressed) {
    return {
      judgmentIllegitimate: false,
      blockThresholdChanges: false,
      stewardLineageAtRisk: false,
      lineageCorrigibilityFailed: false,
      reasons: [],
    };
  }

  if (ignored) reasons.push("CRK-1.J: steward ignored Reality Veto");
  if (suppressed) reasons.push("RPA-1.2: evidence suppression — constitutional violation");

  return {
    judgmentIllegitimate: true,
    blockThresholdChanges: true,
    stewardLineageAtRisk: true,
    lineageCorrigibilityFailed: suppressed || receipt.severity === "critical",
    reasons,
  };
}

/** Continuity Ledger store for Reality Veto receipts. */
export class InMemoryRealityVetoLedger {
  private receipts: RealityVetoReceipt[] = [];

  append(receipt: RealityVetoReceipt): void {
    this.receipts.push(receipt);
  }

  queryByObserver(observerId: Id): RealityVetoReceipt[] {
    return this.receipts.filter((r) => r.observerId === observerId);
  }

  queryPending(): RealityVetoReceipt[] {
    return [...this.receipts];
  }

  list(): RealityVetoReceipt[] {
    return [...this.receipts];
  }
}
