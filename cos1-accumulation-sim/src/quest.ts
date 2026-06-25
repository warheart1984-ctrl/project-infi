import type { RAState } from "./domain.js";
import type { WorldChange } from "./wck.js";

export type QuestTriggerType = "DRIFT" | "SURPASSMENT" | "VALIDATION" | "GOVERNANCE";

export interface QuestTrigger {
  type: QuestTriggerType;
  condition: string;
}

export interface QuestRole {
  id: string;
  label: string;
  minPlayers: number;
  maxPlayers: number;
}

export interface QuestReward {
  type: "XP" | "ITEM" | "TITLE" | "STEWARD_SCORE";
  amount?: number;
  itemId?: string;
  titleId?: string;
}

export interface QuestTemplate {
  id: string;
  name: string;
  description: string;
  trigger: QuestTrigger;
  roles: QuestRole[];
  objectives: string[];
  rewards: QuestReward[];
}

export interface QuestEvaluationContext {
  driftAggregatePSD: number | null;
  affectsSystems: string[];
  hasProvisionalChange: boolean;
  hasValidatedChange: boolean;
  stewardEmergence: boolean;
}

export function defaultQuestTemplates(): QuestTemplate[] {
  return [
    {
      id: "Q_FIX_MAGIC_DRIFT",
      name: "Stabilize the Weave",
      description: "Magic has become unstable; investigate and correct the anomaly.",
      trigger: {
        type: "DRIFT",
        condition: "drift.aggregatePSD > 0.6 && affectsSystems.includes('magic')",
      },
      roles: [
        { id: "INVESTIGATOR", label: "Investigator", minPlayers: 1, maxPlayers: 3 },
        { id: "REFORMER", label: "Reformer", minPlayers: 1, maxPlayers: 2 },
      ],
      objectives: [
        "Collect evidence of unstable spells",
        "Propose a corrective rule",
        "Test the new rule in the field",
      ],
      rewards: [
        { type: "XP", amount: 500 },
        { type: "STEWARD_SCORE", amount: 10 },
      ],
    },
    {
      id: "Q_STEWARD_EMERGENCE",
      name: "Call of Stewardship",
      description: "The world needs governors who can see phenomena and shape the lineage.",
      trigger: {
        type: "GOVERNANCE",
        condition: "stewardEmergence == false && mat3 == true",
      },
      roles: [{ id: "CANDIDATE", label: "Steward Candidate", minPlayers: 1, maxPlayers: 5 }],
      objectives: ["Demonstrate PLA insight", "Integrate as LA", "Perform governance move"],
      rewards: [{ type: "STEWARD_SCORE", amount: 25 }],
    },
  ];
}

/** Minimal expression evaluator for quest trigger conditions */
export function evaluateQuestCondition(
  condition: string,
  ctx: QuestEvaluationContext,
): boolean {
  const drift = ctx.driftAggregatePSD ?? 0;

  if (condition.includes("drift.aggregatePSD > 0.6")) {
    const magic = condition.includes("magic")
      ? ctx.affectsSystems.includes("magic")
      : true;
    return drift > 0.6 && magic;
  }
  if (condition.includes("stewardEmergence == false && mat3 == true")) {
    return !ctx.stewardEmergence;
  }
  if (condition.includes("hasProvisionalChange")) {
    return ctx.hasProvisionalChange;
  }
  if (condition.includes("hasValidatedChange")) {
    return ctx.hasValidatedChange;
  }
  return false;
}

export function evaluateQuestTriggers(
  templates: QuestTemplate[],
  ctx: QuestEvaluationContext,
): QuestTemplate[] {
  return templates.filter((t) => evaluateQuestCondition(t.trigger.condition, ctx));
}

export function buildQuestContext(
  kernel: RAState,
  worldChanges: Record<string, WorldChange>,
  affectsSystems: string[],
): QuestEvaluationContext {
  const changes = Object.values(worldChanges);
  return {
    driftAggregatePSD: kernel.continuity.drift?.aggregatePSD ?? null,
    affectsSystems,
    hasProvisionalChange: changes.some((c) => c.status === "PROVISIONAL"),
    hasValidatedChange: changes.some((c) => c.status === "VALIDATED"),
    stewardEmergence: kernel.continuity.thresholds.stewardEmergence,
  };
}
