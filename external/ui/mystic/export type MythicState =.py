export type MythicState =
  | "lost"
  | "burdened"
  | "seeking"
  | "struggling"
  | "awakening"
  | "building"
  | "transforming"
  | "steady";
export type Archetype =
  | "hero"
  | "shadow"
  | "guide"
  | "builder"
  | "trickster"
  | "witness";
export type MythicReading = {
  state: MythicState;
  dominantArchetype: Archetype;
  opposingArchetype: Archetype;
  trial: string;
  nextAction: string;
  meaning: string;
  risk: string;
};
type Memory = {
  recentStates: MythicState[];
  recentActions: string[];
  repeatedPatterns: string[];
};

export function detectState(input: string): MythicState {
  const text = input.toLowerCase();

  if (text.includes("survive") || text.includes("barely")) return "burdened";
  if (text.includes("stuck") || text.includes("nothing")) return "lost";
  if (text.includes("idea") || text.includes("change everything")) return "awakening";
  if (text.includes("build") || text.includes("system")) return "building";

  return "seeking";
}

export function assignArchetypes(state: MythicState) {
  switch (state) {
    case "lost":
      return { dominantArchetype: "shadow", opposingArchetype: "guide" };
    case "burdened":
      return { dominantArchetype: "shadow", opposingArchetype: "builder" };
    case "awakening":
      return { dominantArchetype: "guide", opposingArchetype: "trickster" };
    case "building":
      return { dominantArchetype: "builder", opposingArchetype: "shadow" };
    default:
      return { dominantArchetype: "witness", opposingArchetype: "trickster" };
  }
}

export function generateTrial(state: MythicState): string {
  switch (state) {
    case "lost":
      return "Meaning vs numbness";
    case "burdened":
      return "Survival vs collapse";
    case "awakening":
      return "Vision vs distraction";
    case "building":
      return "Discipline vs inconsistency";
    default:
      return "Action vs avoidance";
  }
}

export function suggestNextAction(state: MythicState): string {
  switch (state) {
    case "lost":
      return "Complete one grounding action in the next hour.";
    case "burdened":
      return "Do one survival action: water, food, walk, or rest.";
    case "awakening":
      return "Write the idea clearly in five sentences.";
    case "building":
      return "Finish one concrete system task today.";
    default:
      return "Choose one small action and complete it fully.";
  }
}

export function mythicEngine(input: string, memory: Memory): MythicReading {
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
    meaning: `Current growth path is ${trial.toLowerCase()}.`,
    risk: "Inaction strengthens the current negative pattern."
  };
}
type Memory = {
  recentStates: MythicState[];
  recentActions: string[];
  repeatedPatterns: string[];
};

export function detectState(input: string): MythicState {
  const text = input.toLowerCase();

  if (text.includes("survive") || text.includes("barely")) return "burdened";
  if (text.includes("stuck") || text.includes("nothing")) return "lost";
  if (text.includes("idea") || text.includes("change everything")) return "awakening";
  if (text.includes("build") || text.includes("system")) return "building";

  return "seeking";
}

export function assignArchetypes(state: MythicState) {
  switch (state) {
    case "lost":
      return { dominantArchetype: "shadow", opposingArchetype: "guide" };
    case "burdened":
      return { dominantArchetype: "shadow", opposingArchetype: "builder" };
    case "awakening":
      return { dominantArchetype: "guide", opposingArchetype: "trickster" };
    case "building":
      return { dominantArchetype: "builder", opposingArchetype: "shadow" };
    default:
      return { dominantArchetype: "witness", opposingArchetype: "trickster" };
  }
}

export function generateTrial(state: MythicState): string {
  switch (state) {
    case "lost":
      return "Meaning vs numbness";
    case "burdened":
      return "Survival vs collapse";
    case "awakening":
      return "Vision vs distraction";
    case "building":
      return "Discipline vs inconsistency";
    default:
      return "Action vs avoidance";
  }
}

export function suggestNextAction(state: MythicState): string {
  switch (state) {
    case "lost":
      return "Complete one grounding action in the next hour.";
    case "burdened":
      return "Do one survival action: water, food, walk, or rest.";
    case "awakening":
      return "Write the idea clearly in five sentences.";
    case "building":
      return "Finish one concrete system task today.";
    default:
      return "Choose one small action and complete it fully.";
  }
}

export function mythicEngine(input: string, memory: Memory): MythicReading {
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
    meaning: `Current growth path is ${trial.toLowerCase()}.`,
    risk: "Inaction strengthens the current negative pattern."
  };
}
