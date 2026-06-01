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

export type JournalEntry = {
  input: string;
  createdAt: string;
  reading: MythicReading;
};