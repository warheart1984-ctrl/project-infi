import type { Id } from "../css2/types";
import type { ConsequenceLedger } from "./consequence-ledger";
import type { DecisionObject, IdentityObject } from "./consequence-kernel";
import { validateK01, validateK21, type KernelLaw, type KernelViolation } from "./consequence-invariants";

export interface InsulatedDecision {
  decision: DecisionObject;
  outcomeIds: Id[];
  reason: string;
}

export interface AntiInsulationResult {
  /** True when no insulated decisions exist — valid CRK-1 state. */
  constitutionallyValid: boolean;
  insulatedDecisions: InsulatedDecision[];
  /** Which kernel law each insulation attempt would violate. */
  violations: KernelViolation[];
}

/**
 * CRK-1.K3 — Anti-Insulation Proof (operational form).
 *
 * An insulated state exists when Execute(d) ⇒ Outcome(o) but replayed evidence
 * cannot affect the judgment lineage that authorized d. Such a state must violate K0, K1, or K2.
 */
export async function detectInsulatedDecisions(
  ledger: ConsequenceLedger,
  identity: IdentityObject,
): Promise<InsulatedDecision[]> {
  const decisions = await ledger.getDecisionsByIdentity(identity.id);
  const insulated: InsulatedDecision[] = [];

  for (const decision of decisions) {
    if (!decision.executed) continue;

    const outcomes = await ledger.getOutcomesByDecision(decision.id);
    if (outcomes.length === 0) {
      insulated.push({
        decision,
        outcomeIds: [],
        reason: "executed without outcome — violates K0",
      });
      continue;
    }

    let lineageAffected = false;
    let alreadyInsulated = false;

    for (const outcome of outcomes) {
      if (!outcome.replayable) {
        insulated.push({
          decision,
          outcomeIds: [outcome.id],
          reason: "non-replayable outcome — violates K1",
        });
        alreadyInsulated = true;
        break;
      }

      const replayed = await ledger.getEvidenceByOutcome(outcome.id);
      if (replayed.length === 0) {
        insulated.push({
          decision,
          outcomeIds: [outcome.id],
          reason: "replay yields no evidence — violates K0",
        });
        alreadyInsulated = true;
        break;
      }

      const affectsJudgment = replayed.some(
        (e) =>
          e.admissible &&
          (e.affectsLineageId === identity.lineageId || e.affectsLineageId === identity.id),
      );
      if (affectsJudgment) lineageAffected = true;
    }

    if (!alreadyInsulated && outcomes.length > 0 && !lineageAffected) {
      insulated.push({
        decision,
        outcomeIds: outcomes.map((o) => o.id),
        reason: "consequences cannot reach judgment lineage — violates K2",
      });
    }
  }

  return insulated;
}

/** Map insulation reason to the kernel law it violates (K3 proof sketch). */
export function insulationViolatesLaw(reason: string): KernelLaw {
  if (reason.includes("K0") || reason.includes("no evidence") || reason.includes("without outcome")) {
    return "K0";
  }
  if (reason.includes("K1") || reason.includes("non-replayable")) {
    return "K1";
  }
  return "K2";
}

/**
 * CRK-1.K3 — Prove that any insulated state is constitutionally invalid.
 * Returns violations with the specific kernel law each insulation breaks.
 */
export async function proveAntiInsulation(
  ledger: ConsequenceLedger,
  identity: IdentityObject,
): Promise<AntiInsulationResult> {
  const insulated = await detectInsulatedDecisions(ledger, identity);
  const violations: KernelViolation[] = [];

  for (const item of insulated) {
    const law = insulationViolatesLaw(item.reason);
    violations.push({
      law,
      code: `K3.INSULATION_${law}`,
      message: `CRK-1.K3: insulated state invalid — ${item.reason}`,
      decisionId: item.decision.id,
    });
  }

  // Cross-check with formal validators
  for (const item of insulated) {
    const k0 = await validateK01(ledger, item.decision.id);
    const k2 = await validateK21(ledger, identity, item.decision);
    violations.push(...k0.violations, ...k2.violations);
  }

  const deduped = dedupeViolations(violations);

  return {
    constitutionallyValid: insulated.length === 0,
    insulatedDecisions: insulated,
    violations: deduped,
  };
}

function dedupeViolations(violations: KernelViolation[]): KernelViolation[] {
  const seen = new Set<string>();
  const out: KernelViolation[] = [];
  for (const v of violations) {
    const key = `${v.law}:${v.code}:${v.decisionId ?? ""}:${v.outcomeId ?? ""}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(v);
  }
  return out;
}

/** Narrative proof steps for documentation / audit. */
export const K3_PROOF_STEPS = [
  "Assume insulated state S*: executed Decision d with Outcome o where replay cannot affect Judgment(d).",
  "By K0, Replay(o) must yield Evidence e' — otherwise S* violates K0.",
  "By K1, no valid transition may prevent e' from being admissible to future Decisions.",
  "By K2, e' must affect the Judgment lineage that authorized d.",
  "Therefore S* requires violating K0, K1, or K2 — insulation is outside the constitutional runtime.",
] as const;
