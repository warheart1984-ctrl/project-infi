import {
  GameEvent,
  JPSSContributionEventInput,
  AccumulationType,
  AccumulationTag,
  WorldLayer,
} from "./domain.js";
import type { EpistemicMode } from "./domain.js";

const WORLD_TO_JPSS: Record<WorldLayer, string> = {
  Mechanics: "Continuity",
  Lore: "Transferability",
  Economy: "Governance",
  Politics: "Governance",
  Meta: "Meta",
};

function mapLayer(layer: WorldLayer | string): string {
  if (layer in WORLD_TO_JPSS) {
    return WORLD_TO_JPSS[layer as WorldLayer];
  }
  return layer;
}

function readAccumulationTag(context: Record<string, unknown>): AccumulationTag | undefined {
  const tag = context.accumulationTag;
  if (tag && typeof tag === "object" && !Array.isArray(tag)) {
    return tag as AccumulationTag;
  }
  return undefined;
}

/** Heuristic classifier — replace with richer logic as the game layer matures */
function classifyAccumulation(ev: GameEvent): {
  accumulationType: AccumulationType;
  targetsLayer: WorldLayer;
} {
  if (ev.type === "GOVERNANCE") {
    return { accumulationType: "A2", targetsLayer: "Politics" };
  }
  if (ev.type === "ACTION" && ev.action === "DISCOVER_MECHANIC") {
    return { accumulationType: "A1", targetsLayer: "Mechanics" };
  }
  return { accumulationType: "NONE", targetsLayer: "Meta" };
}

function resolveEpistemicMode(
  ev: GameEvent,
  accumulationType: AccumulationType,
  fromExposure: boolean,
): EpistemicMode | undefined {
  const fromContext = ev.context.epistemicMode;
  if (
    fromContext === "OBSERVATION" ||
    fromContext === "INTERPRETATION" ||
    fromContext === "INTEGRATION" ||
    fromContext === "VALIDATION"
  ) {
    return fromContext;
  }
  if (ev.action.toLowerCase().startsWith("observe") && !fromExposure) {
    return "OBSERVATION";
  }
  if (accumulationType === "NONE" && !fromExposure) {
    return "OBSERVATION";
  }
  return undefined;
}

export function gameEventToJPSS(ev: GameEvent): JPSSContributionEventInput {
  const tag = readAccumulationTag(ev.context);
  const classified = classifyAccumulation(ev);

  const accumulationType = tag?.accumulationType ?? classified.accumulationType;
  const worldLayer = tag?.targetsLayer ?? classified.targetsLayer;
  const targetsLayer = mapLayer(worldLayer);

  const fromExposure =
    typeof ev.context.fromExposure === "boolean"
      ? ev.context.fromExposure
      : typeof ev.context.learnedFramework === "boolean"
        ? ev.context.learnedFramework
        : false;

  const draft: JPSSContributionEventInput = {
    id: ev.id,
    actor: ev.actorId,
    timestamp: ev.timestamp,
    accumulationType,
    targetsLayer,
    fromExposure,
    buildsOn: tag?.buildsOn ?? (Array.isArray(ev.context.buildsOn) ? (ev.context.buildsOn as string[]) : []),
    phenomenonAnchor:
      typeof ev.context.phenomenonAnchor === "string" ? ev.context.phenomenonAnchor : null,
    origin: tag?.origin,
    mode: resolveEpistemicMode(ev, accumulationType, fromExposure),
    governanceBehavior:
      ev.type === "GOVERNANCE"
        ? "validate"
        : (ev.context.governanceBehavior as JPSSContributionEventInput["governanceBehavior"]) ?? null,
  };
  return draft;
}
