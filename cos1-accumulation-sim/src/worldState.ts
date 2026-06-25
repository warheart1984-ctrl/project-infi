import type { RAState } from "./domain.js";
import type {
  Faction,
  GameEvent,
  PlayerProfile,
  WorldChange,
  WorldChangeProposal,
  WorldEvent,
} from "./wck.js";
import type { WorldConstitution } from "./constitution.js";
import type { QuestTemplate } from "./quest.js";
import { defaultConstitution } from "./constitution.js";
import { defaultQuestTemplates } from "./quest.js";
import {
  applyEvent,
  initialState,
  registerChange,
} from "./state.js";
import {
  gameEventToContribution,
  proposalToWorldChange,
  toContinuityHealthResponse,
  worldChangeToLineageChange,
  worldEventToContribution,
} from "./gosAdapter.js";
import {
  buildStewardSignals,
  evaluateStewardPromotion,
} from "./stewardship.js";
import { buildQuestContext, evaluateQuestTriggers } from "./quest.js";

export interface WorldRuntime {
  kernel: RAState;
  worldEvents: WorldEvent[];
  worldChanges: Record<string, WorldChange>;
  players: Record<string, PlayerProfile>;
  factions: Record<string, Faction>;
  constitution: WorldConstitution;
  questTemplates: QuestTemplate[];
  activeQuestIds: string[];
}

export function initialWorldRuntime(): WorldRuntime {
  return {
    kernel: initialState(),
    worldEvents: [],
    worldChanges: {},
    players: {},
    factions: {},
    constitution: defaultConstitution(),
    questTemplates: defaultQuestTemplates(),
    activeQuestIds: [],
  };
}

function ensurePlayer(world: WorldRuntime, actorId: string, name?: string): PlayerProfile {
  if (!world.players[actorId]) {
    world.players[actorId] = {
      id: actorId,
      name: name ?? actorId,
      plaCount: 0,
      laCount: 0,
      saCount: 0,
      reconstructabilityScore: 1,
      stewardshipScore: 0,
      roles: ["CITIZEN"],
    };
  }
  return world.players[actorId];
}

function syncPlayerFromKernel(world: WorldRuntime, actorId: string): void {
  const player = ensurePlayer(world, actorId);
  const events = world.kernel.events.filter((e) => e.actor === actorId);
  let plaCount = 0;
  let laCount = 0;
  let saCount = 0;
  for (const e of events) {
    const origin = world.kernel.eventOrigins[e.id];
    if (origin === "PLA") plaCount++;
    else if (origin === "LA") laCount++;
    else if (origin === "SA") saCount++;
  }

  const reconstructabilityScore = Math.max(
    0,
    1 - world.kernel.continuity.reconstructability.reconstructionCost,
  );

  const validated = Object.values(world.worldChanges).filter(
    (c) => c.status === "VALIDATED" && c.proposedBy === actorId,
  ).length;
  const total = Object.values(world.worldChanges).filter(
    (c) => c.proposedBy === actorId,
  ).length;

  const signals = buildStewardSignals(
    plaCount,
    laCount,
    saCount,
    world.kernel.continuity.pla.plaDepth,
    world.kernel.continuity.la.laDepth,
    reconstructabilityScore,
    validated,
    total,
    world.kernel.continuity.drift?.aggregatePSD ?? null,
  );

  world.players[actorId] = evaluateStewardPromotion(
    {
      ...player,
      plaCount,
      laCount,
      saCount,
      reconstructabilityScore,
    },
    signals,
  );
}

function refreshQuests(world: WorldRuntime): void {
  const systems = Object.values(world.worldChanges).flatMap((c) => c.affectsSystems);
  const ctx = buildQuestContext(world.kernel, world.worldChanges, systems);
  const triggered = evaluateQuestTriggers(world.questTemplates, ctx);
  world.activeQuestIds = triggered.map((q) => q.id);
}

export function ingestGameEvent(world: WorldRuntime, event: GameEvent): WorldRuntime {
  const contribution = gameEventToContribution(event);
  const kernel = applyEvent(world.kernel, contribution);
  const worldEvent: WorldEvent = {
    id: event.id,
    actorId: event.actorId,
    timestamp: event.timestamp,
    type: event.type,
    payload: { action: event.action, ...event.context },
  };
  const next: WorldRuntime = {
    ...world,
    kernel,
    worldEvents: [...world.worldEvents, worldEvent],
  };
  syncPlayerFromKernel(next, event.actorId);
  refreshQuests(next);
  return next;
}

export function ingestWorldEvent(world: WorldRuntime, event: WorldEvent): WorldRuntime {
  const contribution = worldEventToContribution(event);
  const kernel = applyEvent(world.kernel, contribution);
  const next: WorldRuntime = {
    ...world,
    kernel,
    worldEvents: [...world.worldEvents, event],
  };
  syncPlayerFromKernel(next, event.actorId);
  refreshQuests(next);
  return next;
}

export function proposeWorldChange(
  world: WorldRuntime,
  proposal: WorldChangeProposal,
): WorldRuntime {
  const change = proposalToWorldChange(proposal);
  let kernel = registerChange(world.kernel, worldChangeToLineageChange(change));
  return {
    ...world,
    kernel,
    worldChanges: { ...world.worldChanges, [change.id]: change },
  };
}

export function getWorldHistory(
  world: WorldRuntime,
  status?: WorldChange["status"] | "ALL",
): WorldChange[] {
  const all = Object.values(world.worldChanges);
  if (!status || status === "ALL") return all;
  return all.filter((c) => c.status === status);
}

export function getContinuityHealth(world: WorldRuntime) {
  return toContinuityHealthResponse(world.kernel);
}

export function getActiveQuests(world: WorldRuntime): QuestTemplate[] {
  return world.questTemplates.filter((q) => world.activeQuestIds.includes(q.id));
}
