const NON_CONCRETE_PATTERNS = [
  /^witness:?$/i,
  /^witness:\s*present\.?$/i,
  /^present\.?$/i,
  /^(trace|seal|sigil|echo|mode|intent)\s*:/i,
];

const CONCRETE_CUE_PATTERN =
  /\b(i|my|the|this|that|here|there|on|in|at|under|over|near|inside|outside|before|after|behind|feel|felt|see|saw|hear|heard|touch|touched|smell|smelled|taste|tasted|is|are|was|were|has|have)\b/i;

function normalizeLine(line: string): string {
  return line
    .trim()
    .replace(/^[-*]\s+/, "")
    .trim();
}

function splitWords(line: string): string[] {
  return line.match(/[a-z][a-z0-9'-]*/gi) || [];
}

export function splitWitnessPayloadLines(utterance: string): string[] {
  return utterance
    .split(/\r?\n+/)
    .map((line) => normalizeLine(line))
    .filter(Boolean)
    .filter((line) => !/^witness:?$/i.test(line));
}

export function isConcreteWitnessLine(line: string): boolean {
  const normalized = normalizeLine(line);
  if (!normalized) return false;
  if (NON_CONCRETE_PATTERNS.some((pattern) => pattern.test(normalized))) {
    return false;
  }

  const words = splitWords(normalized);
  if (words.length < 2) return false;
  if (CONCRETE_CUE_PATTERN.test(normalized)) return true;

  return words.length >= 6;
}

export function hasConcreteWitnessLine(utterance: string): boolean {
  return splitWitnessPayloadLines(utterance).some((line) => isConcreteWitnessLine(line));
}
