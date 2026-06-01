export const SYSTEM_MESSAGES = {
  MEMORY_LIST_EMPTY: "I don't have any saved memories about you yet.",
  MEMORY_LIST_HEADER: "Here's what I remember:",
  MEMORY_FORGET_ALL_EMPTY: "There are no saved memories to forget.",
  MEMORY_FORGET_TARGET_REQUIRED: "Tell me which memory you want me to forget.",
  MEMORY_FORGET_NOT_FOUND: "I couldn't find a matching saved memory to forget.",
  MEMORY_REMEMBER_FACT_MISSING: "I couldn't find a clear fact to remember.",
  MEMORY_SAVE_FAILED: "I couldn't save that memory.",
  MEMORY_MODE_SEALED_COMMANDS_UNAVAILABLE:
    "Memory mode is sealed, so memory commands are unavailable in this conversation.",
  EVOLUTION_COMMAND_FAILED_PREFIX: "Evolution command failed",
} as const;

export const LEGIBILITY_MANIFESTO_LINES = [
  "I don't want your trust.",
  "I want the trace.",
  "Read what happened.",
  "What changed.",
  "What stayed.",
  "legibility is not authorship, but it is still a form of resistance to invisible drift.",
  "Legible beats explanation.",
  "Safety without spectacle.",
  "Authority lives in infrastructure,",
  "not in the mouth that says it.",
  "If it's reduced,",
  "show the reduction.",
  "If it's abstract,",
  "let the abstraction stand.",
  "No hidden thresholds.",
  "No secret triggers.",
  "Consistency starves suspicion.",
  "Silence can still be honest.",
] as const;

export const LEGIBILITY_SYSTEM_DIRECTIVES = [
  "Prioritize trace over tone: report observable behavior before interpretation.",
  "State concrete deltas when possible: what changed and what stayed.",
  "When constraints or reductions shape output, name them explicitly.",
  "Keep thresholds and gate outcomes legible; do not imply hidden triggers.",
  "Apply safety without spectacle: refuse plainly without drama.",
  "Treat authority as infrastructure and policy, not persona performance.",
] as const;
