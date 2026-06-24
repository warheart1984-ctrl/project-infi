import type { Id } from "../css2/types";
import type {
  ConsequenceTransition,
  DecisionObject,
  EvidenceObject,
  IdentityObject,
  OutcomeObject,
  ResourceObject,
} from "./consequence-kernel";

/** Append-only store for consequence transmission objects and transitions. */
export interface ConsequenceLedger {
  putIdentity(identity: IdentityObject): Promise<void>;
  putEvidence(evidence: EvidenceObject): Promise<void>;
  putDecision(decision: DecisionObject): Promise<void>;
  putResource(resource: ResourceObject): Promise<void>;
  putOutcome(outcome: OutcomeObject): Promise<void>;
  appendTransition(transition: ConsequenceTransition): Promise<void>;

  getIdentity(id: Id): Promise<IdentityObject | null>;
  getEvidence(id: Id): Promise<EvidenceObject | null>;
  getDecision(id: Id): Promise<DecisionObject | null>;
  getResource(id: Id): Promise<ResourceObject | null>;
  getOutcome(id: Id): Promise<OutcomeObject | null>;

  getOutcomesByDecision(decisionId: Id): Promise<OutcomeObject[]>;
  getEvidenceByOutcome(outcomeId: Id): Promise<EvidenceObject[]>;
  getDecisionsByIdentity(identityId: Id): Promise<DecisionObject[]>;
  listTransitions(): Promise<ConsequenceTransition[]>;
}

export class InMemoryConsequenceLedger implements ConsequenceLedger {
  private identities = new Map<Id, IdentityObject>();
  private evidence = new Map<Id, EvidenceObject>();
  private decisions = new Map<Id, DecisionObject>();
  private resources = new Map<Id, ResourceObject>();
  private outcomes = new Map<Id, OutcomeObject>();
  private transitions: ConsequenceTransition[] = [];

  async putIdentity(identity: IdentityObject): Promise<void> {
    this.identities.set(identity.id, identity);
  }

  async putEvidence(evidence: EvidenceObject): Promise<void> {
    this.evidence.set(evidence.id, evidence);
  }

  async putDecision(decision: DecisionObject): Promise<void> {
    this.decisions.set(decision.id, decision);
  }

  async putResource(resource: ResourceObject): Promise<void> {
    this.resources.set(resource.id, resource);
  }

  async putOutcome(outcome: OutcomeObject): Promise<void> {
    this.outcomes.set(outcome.id, outcome);
  }

  async appendTransition(transition: ConsequenceTransition): Promise<void> {
    this.transitions.push(transition);
  }

  async getIdentity(id: Id): Promise<IdentityObject | null> {
    return this.identities.get(id) ?? null;
  }

  async getEvidence(id: Id): Promise<EvidenceObject | null> {
    return this.evidence.get(id) ?? null;
  }

  async getDecision(id: Id): Promise<DecisionObject | null> {
    return this.decisions.get(id) ?? null;
  }

  async getResource(id: Id): Promise<ResourceObject | null> {
    return this.resources.get(id) ?? null;
  }

  async getOutcome(id: Id): Promise<OutcomeObject | null> {
    return this.outcomes.get(id) ?? null;
  }

  async getOutcomesByDecision(decisionId: Id): Promise<OutcomeObject[]> {
    return [...this.outcomes.values()].filter((o) => o.decisionId === decisionId);
  }

  async getEvidenceByOutcome(outcomeId: Id): Promise<EvidenceObject[]> {
    return [...this.evidence.values()].filter((e) => e.sourceOutcomeId === outcomeId);
  }

  async getDecisionsByIdentity(identityId: Id): Promise<DecisionObject[]> {
    return [...this.decisions.values()].filter((d) => d.identityId === identityId);
  }

  async listTransitions(): Promise<ConsequenceTransition[]> {
    return [...this.transitions];
  }
}
