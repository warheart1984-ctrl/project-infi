import type { Id } from "../css2/types";
import type { ConsequenceLedger } from "./consequence-ledger";
import type {
  ConsequenceTransition,
  DecisionObject,
  EvidenceObject,
  IdentityObject,
  OutcomeObject,
} from "./consequence-kernel";

export type KernelLaw = "K0" | "K1" | "K2";

export interface KernelViolation {
  law: KernelLaw;
  code: string;
  message: string;
  decisionId?: Id;
  outcomeId?: Id;
  evidenceId?: Id;
  transitionId?: Id;
}

export interface KernelValidationResult {
  valid: boolean;
  violations: KernelViolation[];
}

/** K0.1 — Execute(d) ⇒ ∃o,e': Outcome(o) ∧ Replay(o) ⇒ Evidence(e'). */
export async function validateK01(
  ledger: ConsequenceLedger,
  decisionId: Id,
): Promise<KernelValidationResult> {
  const violations: KernelViolation[] = [];
  const decision = await ledger.getDecision(decisionId);
  if (!decision) {
    return {
      valid: false,
      violations: [
        {
          law: "K0",
          code: "K0.MISSING_DECISION",
          message: `Decision ${decisionId} not found`,
          decisionId,
        },
      ],
    };
  }

  if (!decision.executed) {
    return { valid: true, violations: [] };
  }

  const outcomes = await ledger.getOutcomesByDecision(decisionId);
  if (outcomes.length === 0) {
    violations.push({
      law: "K0",
      code: "K0.NO_OUTCOME",
      message: "CRK-1.K0.1: executed decision has no outcome — no execution without replayable consequence",
      decisionId,
    });
    return { valid: false, violations };
  }

  for (const outcome of outcomes) {
    if (!outcome.replayable) {
      violations.push({
        law: "K0",
        code: "K0.NON_REPLAYABLE_OUTCOME",
        message: "CRK-1.K0: outcome is not replayable",
        decisionId,
        outcomeId: outcome.id,
      });
      continue;
    }

    const replayEvidence = await ledger.getEvidenceByOutcome(outcome.id);
    if (replayEvidence.length === 0 && !outcome.replayedToEvidenceId) {
      violations.push({
        law: "K0",
        code: "K0.NO_REPLAY_EVIDENCE",
        message:
          "CRK-1.K0.1: executed outcome has no replayed evidence — Replay(o) must yield Evidence(e')",
        decisionId,
        outcomeId: outcome.id,
      });
    }
  }

  return { valid: violations.length === 0, violations };
}

export type SeverabilityKind =
  | "drop_outcome"
  | "block_replay"
  | "quarantine_evidence"
  | "execute_without_outcome";

/** K1.1 — No valid transition may sever Decision→Outcome→Evidence. */
export function assessSeverability(transition: ConsequenceTransition): SeverabilityKind | null {
  if (transition.kind === "execute_decision" && !transition.outputIds.outcome) {
    return "execute_without_outcome";
  }
  if (transition.kind === "replay_outcome" && !transition.outputIds.evidence) {
    return "block_replay";
  }
  return null;
}

export function validateTransitionK11(transition: ConsequenceTransition): KernelValidationResult {
  const sever = assessSeverability(transition);
  if (!sever) return { valid: true, violations: [] };

  const messages: Record<SeverabilityKind, string> = {
    drop_outcome: "CRK-1.K1: transition drops outcome — unrecorded execution",
    block_replay: "CRK-1.K1: transition blocks replay — outcome not admissible as evidence",
    quarantine_evidence: "CRK-1.K1: evidence quarantined — not admissible to future decisions",
    execute_without_outcome: "CRK-1.K1: decision executed without creating outcome",
  };

  return {
    valid: false,
    violations: [
      {
        law: "K1",
        code: `K1.${sever.toUpperCase()}`,
        message: messages[sever],
        transitionId: transition.id,
      },
    ],
  };
}

/** Object-level K1 checks (non-replayable outcome, inadmissible evidence). */
export function validateObjectK11(params: {
  outcome?: OutcomeObject;
  evidence?: EvidenceObject;
  decision?: DecisionObject;
}): KernelValidationResult {
  const violations: KernelViolation[] = [];

  if (params.outcome && !params.outcome.replayable) {
    violations.push({
      law: "K1",
      code: "K1.NON_REPLAYABLE_OUTCOME",
      message: "CRK-1.K1: outcome marked non-replayable",
      outcomeId: params.outcome.id,
      decisionId: params.outcome.decisionId,
    });
  }

  if (params.evidence && !params.evidence.admissible) {
    violations.push({
      law: "K1",
      code: "K1.QUARANTINED_EVIDENCE",
      message: "CRK-1.K1: evidence marked ineligible for future decisions",
      evidenceId: params.evidence.id,
    });
  }

  if (params.decision?.executed && params.outcome === undefined) {
    violations.push({
      law: "K1",
      code: "K1.EXECUTE_WITHOUT_OUTCOME",
      message: "CRK-1.K1: executed decision without outcome object",
      decisionId: params.decision.id,
    });
  }

  return { valid: violations.length === 0, violations };
}

/** K2.1 — Cost binding: Authorize(i,d) ⇒ outcome coupled and replay affects lineage. */
export async function validateK21(
  ledger: ConsequenceLedger,
  identity: IdentityObject,
  decision: DecisionObject,
): Promise<KernelValidationResult> {
  const violations: KernelViolation[] = [];

  if (decision.identityId !== identity.id) {
    violations.push({
      law: "K2",
      code: "K2.IDENTITY_MISMATCH",
      message: "CRK-1.K2: decision not traceable to authorizing identity",
      decisionId: decision.id,
    });
    return { valid: false, violations };
  }

  if (!decision.executed) {
    return { valid: true, violations: [] };
  }

  const outcomes = await ledger.getOutcomesByDecision(decision.id);
  if (outcomes.length === 0) {
    violations.push({
      law: "K2",
      code: "K2.NO_OUTCOME_COUPLING",
      message: "CRK-1.K2: decision not coupled to outcome",
      decisionId: decision.id,
    });
    return { valid: false, violations };
  }

  for (const outcome of outcomes) {
    const replayed = await ledger.getEvidenceByOutcome(outcome.id);
    const affecting = replayed.filter(
      (e) =>
        e.affectsLineageId === identity.lineageId ||
        e.affectsLineageId === identity.id,
    );

    if (affecting.length === 0) {
      violations.push({
        law: "K2",
        code: "K2.NO_LINEAGE_BINDING",
        message:
          "CRK-1.K2.1: replayed evidence does not affect authorizing judgment lineage — cost not bound",
        decisionId: decision.id,
        outcomeId: outcome.id,
      });
    }

    for (const e of replayed) {
      if (!e.admissible) {
        violations.push({
          law: "K2",
          code: "K2.EVIDENCE_INVISIBLE",
          message: "CRK-1.K2: lineage cannot mark consequence evidence as non-binding",
          evidenceId: e.id,
          decisionId: decision.id,
        });
      }
    }
  }

  return { valid: violations.length === 0, violations };
}

/** Validate full consequence chain for a decision against K0, K1, K2. */
export async function validateConsequenceChain(
  ledger: ConsequenceLedger,
  identity: IdentityObject,
  decisionId: Id,
): Promise<KernelValidationResult> {
  const decision = await ledger.getDecision(decisionId);
  if (!decision) {
    return {
      valid: false,
      violations: [
        {
          law: "K0",
          code: "K0.MISSING_DECISION",
          message: `Decision ${decisionId} not found`,
          decisionId,
        },
      ],
    };
  }

  const k0 = await validateK01(ledger, decisionId);
  const k2 = await validateK21(ledger, identity, decision);
  const outcomes = await ledger.getOutcomesByDecision(decisionId);
  const objectK1 = outcomes.flatMap((o) => validateObjectK11({ outcome: o }).violations);

  const transitions = await ledger.listTransitions();
  const transitionK1 = transitions
    .filter((t) => t.inputIds.decision === decisionId || t.outputIds.outcome)
    .flatMap((t) => validateTransitionK11(t).violations);

  const violations = [...k0.violations, ...k2.violations, ...objectK1, ...transitionK1];
  return { valid: violations.length === 0, violations };
}
