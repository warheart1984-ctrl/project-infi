import { MythicReading, MythicState, Archetype } from "@/lib/types";
      return { dominantArchetype: "hero", opposingArchetype: "shadow" };
    case "steady":
      return { dominantArchetype: "builder", opposingArchetype: "trickster" };
    default:
      return { dominantArchetype: "witness", opposingArchetype: "trickster" };
  }
}

export function generateTrial(state: MythicState): string {
  switch (state) {
    case "lost":
      return "Meaning vs numbness";
    case "burdened":
      return "Guilt vs understanding";
    case "struggling":
      return "Survival vs collapse";
    case "awakening":
      return "Vision vs distraction";
    case "building":
      return "Discipline vs inconsistency";
    case "transforming":
      return "Reaction vs control";
    case "steady":
      return "Maintenance vs drift";
    default:
      return "Action vs avoidance";
  }
}

export function suggestNextAction(state: MythicState): string {
  switch (state) {
    case "lost":
      return "Complete one grounding action in the next hour.";
    case "burdened":
      return "Name the guilt clearly and replace self-attack with one honest sentence.";
    case "struggling":
      return "Do one survival action now: water, food, walk, or rest.";
    case "awakening":
      return "Write the idea clearly in five sentences.";
    case "building":
      return "Finish one concrete system task today.";
    case "transforming":
      return "Pause for 10 seconds before acting when anger rises.";
    case "steady":
      return "Reinforce your daily protocol and track one win before bed.";
    default:
      return "Choose one small action and complete it fully.";
  }
}

export function mythicEngine(input: string): MythicReading {
  const state = detectState(input);
  const { dominantArchetype, opposingArchetype } = assignArchetypes(state);
  const trial = generateTrial(state);
  const nextAction = suggestNextAction(state);

  return {
    state,
    dominantArchetype,
    opposingArchetype,
    trial,
    nextAction,
    meaning: `Your current path is ${trial.toLowerCase()}.`,
    risk: "Inaction reinforces the current negative pattern.",
  };
}