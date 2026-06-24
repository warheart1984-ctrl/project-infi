import type { Id, ISOTime } from "../css2/types";

/** CRK-1.K0 — Consequence Transmission Kernel objects. */

export interface IdentityObject {
  id: Id;
  /** Stewardship lineage for K2 cost binding across successors. */
  lineageId: Id;
  timestamp: ISOTime;
  label?: string;
}

export interface EvidenceObject {
  id: Id;
  timestamp: ISOTime;
  payload: unknown;
  /** Source outcome when produced via ReplayOutcome (K0). */
  sourceOutcomeId?: Id;
  /** K1 — evidence must remain admissible to future decisions unless transition is invalid. */
  admissible: boolean;
  /** Identity lineage this evidence may affect (K2). */
  affectsLineageId?: Id;
}

export interface DecisionObject {
  id: Id;
  identityId: Id;
  evidenceIds: Id[];
  timestamp: ISOTime;
  payload: unknown;
  committed: boolean;
  executed: boolean;
}

export interface ResourceObject {
  id: Id;
  decisionId: Id;
  timestamp: ISOTime;
  payload: unknown;
  allocated: boolean;
}

export interface OutcomeObject {
  id: Id;
  decisionId: Id;
  resourceId: Id;
  timestamp: ISOTime;
  payload: unknown;
  /** K1 — outcomes must be replayable; non-replayable outcomes are constitutionally invalid. */
  replayable: boolean;
  /** Evidence id produced by ReplayOutcome, when replay has occurred. */
  replayedToEvidenceId?: Id;
}

export type ConsequenceTransitionKind =
  | "propose_decision"
  | "allocate_resource"
  | "execute_decision"
  | "replay_outcome";

export interface ConsequenceTransition {
  id: Id;
  kind: ConsequenceTransitionKind;
  timestamp: ISOTime;
  inputIds: Record<string, Id>;
  outputIds: Record<string, Id>;
}

export interface ProposeDecisionInput {
  identity: IdentityObject;
  evidence: EvidenceObject[];
  payload?: unknown;
  timestamp?: ISOTime;
}

export interface AllocateResourceInput {
  decision: DecisionObject;
  resource: Omit<ResourceObject, "allocated" | "decisionId" | "timestamp"> & {
    timestamp?: ISOTime;
  };
}

export interface ExecuteDecisionInput {
  decision: DecisionObject;
  resource: ResourceObject;
  outcome: Omit<OutcomeObject, "decisionId" | "resourceId" | "replayable" | "timestamp"> & {
    replayable?: boolean;
    timestamp?: ISOTime;
  };
}

export interface ReplayOutcomeInput {
  outcome: OutcomeObject;
  evidence: Omit<EvidenceObject, "sourceOutcomeId" | "admissible" | "timestamp"> & {
    admissible?: boolean;
    timestamp?: ISOTime;
  };
  /** Lineage that must be able to receive this evidence (K2). */
  affectsLineageId: Id;
}

function nowIso(): ISOTime {
  return new Date().toISOString();
}

function newId(prefix: string): Id {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

/** ProposeDecision(Identity, Evidence) → Decision */
export function proposeDecision(input: ProposeDecisionInput): {
  decision: DecisionObject;
  transition: ConsequenceTransition;
} {
  const timestamp = input.timestamp ?? nowIso();
  const inadmissible = input.evidence.filter((e) => !e.admissible);
  if (inadmissible.length > 0) {
    throw new Error(
      `CRK-1.K1: cannot propose decision with inadmissible evidence: ${inadmissible.map((e) => e.id).join(", ")}`,
    );
  }

  const decision: DecisionObject = {
    id: newId("dec"),
    identityId: input.identity.id,
    evidenceIds: input.evidence.map((e) => e.id),
    timestamp,
    payload: input.payload ?? { evidenceIds: input.evidence.map((e) => e.id) },
    committed: true,
    executed: false,
  };

  const transition: ConsequenceTransition = {
    id: newId("tx"),
    kind: "propose_decision",
    timestamp,
    inputIds: {
      identity: input.identity.id,
      evidence: input.evidence[0]?.id ?? "",
    },
    outputIds: { decision: decision.id },
  };

  return { decision, transition };
}

/** AllocateResource(Decision, Resource) → Resource */
export function allocateResource(input: AllocateResourceInput): {
  resource: ResourceObject;
  transition: ConsequenceTransition;
} {
  if (!input.decision.committed) {
    throw new Error("CRK-1.K0: cannot allocate resource for uncommitted decision");
  }

  const timestamp = input.resource.timestamp ?? nowIso();
  const resource: ResourceObject = {
    id: input.resource.id ?? newId("res"),
    decisionId: input.decision.id,
    timestamp,
    payload: input.resource.payload,
    allocated: true,
  };

  const transition: ConsequenceTransition = {
    id: newId("tx"),
    kind: "allocate_resource",
    timestamp,
    inputIds: { decision: input.decision.id, resource: resource.id },
    outputIds: { resource: resource.id },
  };

  return { resource, transition };
}

/** ExecuteDecision(Decision, Resource) → Outcome */
export function executeDecision(input: ExecuteDecisionInput): {
  outcome: OutcomeObject;
  decision: DecisionObject;
  transition: ConsequenceTransition;
} {
  if (!input.decision.committed) {
    throw new Error("CRK-1.K0: cannot execute uncommitted decision");
  }
  if (!input.resource.allocated || input.resource.decisionId !== input.decision.id) {
    throw new Error("CRK-1.K0: resource must be allocated to this decision");
  }

  const timestamp = input.outcome.timestamp ?? nowIso();
  const replayable = input.outcome.replayable ?? true;
  if (!replayable) {
    throw new Error("CRK-1.K1: outcome must be replayable — non-replayable execution is invalid");
  }

  const outcome: OutcomeObject = {
    id: input.outcome.id ?? newId("out"),
    decisionId: input.decision.id,
    resourceId: input.resource.id,
    timestamp,
    payload: input.outcome.payload,
    replayable: true,
  };

  const decision: DecisionObject = { ...input.decision, executed: true };

  const transition: ConsequenceTransition = {
    id: newId("tx"),
    kind: "execute_decision",
    timestamp,
    inputIds: { decision: input.decision.id, resource: input.resource.id },
    outputIds: { outcome: outcome.id },
  };

  return { outcome, decision, transition };
}

/** ReplayOutcome(Outcome) → Evidence' */
export function replayOutcome(input: ReplayOutcomeInput): {
  evidence: EvidenceObject;
  outcome: OutcomeObject;
  transition: ConsequenceTransition;
} {
  if (!input.outcome.replayable) {
    throw new Error("CRK-1.K1: cannot replay non-replayable outcome");
  }

  const timestamp = input.evidence.timestamp ?? nowIso();
  const admissible = input.evidence.admissible ?? true;
  if (!admissible) {
    throw new Error("CRK-1.K1: replayed evidence must be admissible to future decisions");
  }

  const evidence: EvidenceObject = {
    id: input.evidence.id ?? newId("ev"),
    timestamp,
    payload: input.evidence.payload ?? input.outcome.payload,
    sourceOutcomeId: input.outcome.id,
    admissible: true,
    affectsLineageId: input.affectsLineageId,
  };

  const outcome: OutcomeObject = {
    ...input.outcome,
    replayedToEvidenceId: evidence.id,
  };

  const transition: ConsequenceTransition = {
    id: newId("tx"),
    kind: "replay_outcome",
    timestamp,
    inputIds: { outcome: input.outcome.id },
    outputIds: { evidence: evidence.id },
  };

  return { evidence, outcome, transition };
}
