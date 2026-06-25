import type { JPSSContributionEvent, LineageChange, AccumulationType } from "./domain.js";
import type {
  AccumulationTag,
  GameEvent,
  WorldChange,
  WorldChangeProposal,
  WorldLayer,
  WorldEvent,
  ContinuityHealthResponse,
} from "./wck.js";
import type { RAState, JPSSContributionEventInput } from "./domain.js";
import { gameEventToJPSS } from "./gameAdapter.js";
import { withEventTags } from "./epistemicClassifier.js";

const LAYER_MAP: Record<WorldLayer, string> = {
  Mechanics: "Continuity",
  Lore: "Transferability",
  Economy: "Governance",
  Politics: "Governance",
  Meta: "Meta",
};

export function mapWorldLayer(layer: WorldLayer): string {
  return LAYER_MAP[layer];
}

function readString(ctx: Record<string, unknown>, key: string): string | undefined {
  const v = ctx[key];
  return typeof v === "string" ? v : undefined;
}

function readBool(ctx: Record<string, unknown>, key: string): boolean | undefined {
  const v = ctx[key];
  return typeof v === "boolean" ? v : undefined;
}

function readTag(ctx: Record<string, unknown>): Partial<AccumulationTag> | undefined {
  const tag = ctx.accumulationTag;
  if (tag && typeof tag === "object" && !Array.isArray(tag)) {
    return tag as Partial<AccumulationTag>;
  }
  return undefined;
}

export function extractAccumulationTag(
  gameEvent: GameEvent | WorldEvent,
): Partial<AccumulationTag> | undefined {
  const payload = "context" in gameEvent ? gameEvent.context : gameEvent.payload;
  return readTag(payload);
}

export function gameEventToContribution(
  ev: GameEvent,
  tagOverride?: Partial<AccumulationTag>,
): JPSSContributionEvent {
  const base = withEventTags(gameEventToJPSS(ev));
  if (!tagOverride) return base;
  const worldLayer = tagOverride.targetsLayer ?? "Meta";
  return {
    ...base,
    accumulationType: tagOverride.accumulationType ?? base.accumulationType,
    targetsLayer: tagOverride.targetsLayer ? mapWorldLayer(worldLayer) : base.targetsLayer,
    buildsOn: tagOverride.buildsOn ?? base.buildsOn,
    origin: tagOverride.origin ?? base.origin,
  };
}

export function worldEventToContribution(ev: WorldEvent): JPSSContributionEvent {
  return gameEventToContribution({
    id: ev.id,
    actorId: ev.actorId,
    timestamp: ev.timestamp,
    type: ev.type,
    action: readString(ev.payload, "action") ?? ev.type,
    context: ev.payload,
  });
}

export function worldChangeToLineageChange(change: WorldChange): LineageChange {
  return {
    id: change.id,
    description: change.description,
    affectsInvariants: change.affectsSystems,
    status: change.status,
    acceptedAt: change.acceptedAt,
    validatedAt: change.validatedAt,
    originType: change.origin,
  };
}

export function proposalToWorldChange(proposal: WorldChangeProposal): WorldChange {
  return {
    id: proposal.id,
    description: proposal.description,
    origin: proposal.origin,
    accumulationType: proposal.accumulationType ?? "A2",
    proposedBy: proposal.proposedBy,
    affectsSystems: proposal.affectsSystems,
    status: "PROVISIONAL",
    acceptedAt: new Date().toISOString(),
    validatedAt: null,
    hypothesis: proposal.hypothesis,
  };
}

export function toContinuityHealthResponse(kernel: RAState): ContinuityHealthResponse {
  const c = kernel.continuity;
  return {
    accumulation: {
      PLA: { count: c.pla.plaCount, actors: c.pla.plaActors },
      LA: { count: c.la.laCount, actors: c.la.laActors },
      SA: { count: c.sa.saCount, actors: c.sa.saActors },
    },
    mat3: c.mat3,
    plt1: c.plt1,
    interpretation: c.interpretation,
    reconstructability: {
      reconstructionCost: c.reconstructability.reconstructionCost,
      reconstructionThreshold: c.reconstructability.reconstructionThreshold,
      k4Satisfied: c.reconstructability.k4Satisfied,
    },
    drift: c.drift ? { aggregatePSD: c.drift.aggregatePSD } : null,
    couplingStrength: c.coupling.couplingStrength,
    epistemic: c.epistemic,
    pla: {
      clustering: c.pla.clustering,
      crossDomainRecurrence: c.pla.crossDomainRecurrence,
      validationSurvival: c.pla.validationSurvival,
      instrumentality: c.pla.instrumentality,
    },
  };
}
