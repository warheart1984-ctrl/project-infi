import type { Id } from "../css2/types";
import type { ConsequenceLedger } from "./consequence-ledger";
import {
  allocateResource,
  executeDecision,
  proposeDecision,
  replayOutcome,
  type EvidenceObject,
  type IdentityObject,
} from "./consequence-kernel";
import { validateConsequenceChain } from "./consequence-invariants";
import { proveAntiInsulation } from "./anti-insulation";

export interface ConsequencePipelineInput {
  identity: IdentityObject;
  evidence: EvidenceObject[];
  resourcePayload?: unknown;
  outcomePayload?: unknown;
  replayPayload?: unknown;
}

export interface ConsequencePipelineResult {
  decisionId: Id;
  outcomeId: Id;
  evidenceId: Id;
  validation: Awaited<ReturnType<typeof validateConsequenceChain>>;
  antiInsulation: Awaited<ReturnType<typeof proveAntiInsulation>>;
}

/**
 * Run the full K0 transition chain and persist to ledger:
 * Propose → Allocate → Execute → Replay.
 */
export async function runConsequencePipeline(
  ledger: ConsequenceLedger,
  input: ConsequencePipelineInput,
): Promise<ConsequencePipelineResult> {
  await ledger.putIdentity(input.identity);
  for (const e of input.evidence) {
    await ledger.putEvidence(e);
  }

  const { decision, transition: t1 } = proposeDecision({
    identity: input.identity,
    evidence: input.evidence,
  });
  await ledger.putDecision(decision);
  await ledger.appendTransition(t1);

  const { resource, transition: t2 } = allocateResource({
    decision,
    resource: { id: `res-${decision.id}`, payload: input.resourcePayload ?? {} },
  });
  await ledger.putResource(resource);
  await ledger.appendTransition(t2);

  const { outcome, decision: executed, transition: t3 } = executeDecision({
    decision,
    resource,
    outcome: { id: `out-${decision.id}`, payload: input.outcomePayload ?? {} },
  });
  await ledger.putDecision(executed);
  await ledger.putOutcome(outcome);
  await ledger.appendTransition(t3);

  const { evidence, outcome: replayed, transition: t4 } = replayOutcome({
    outcome,
    affectsLineageId: input.identity.lineageId,
    evidence: { id: `ev-replay-${outcome.id}`, payload: input.replayPayload ?? outcome.payload },
  });
  await ledger.putEvidence(evidence);
  await ledger.putOutcome(replayed);
  await ledger.appendTransition(t4);

  const validation = await validateConsequenceChain(ledger, input.identity, decision.id);
  const antiInsulation = await proveAntiInsulation(ledger, input.identity);

  return {
    decisionId: decision.id,
    outcomeId: outcome.id,
    evidenceId: evidence.id,
    validation,
    antiInsulation,
  };
}
