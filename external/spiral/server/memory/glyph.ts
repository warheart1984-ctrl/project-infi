export interface GlyphMemory {
  utterance: string;
  impression: string;
  impressionTone: string;
  sigilTags: string[];
  context: {
    trace: string;
    seal: string;
    presenceScore: number;
    invokedAt: string;
    fieldVector: string[];
  };
  recall: number;
}

export interface ResonanceInput {
  utterance: string;
  trace?: string;
  field?: {
    sigils?: string[];
    tone?: string;
    gate?: string;
  };
  memoryWeights?: Partial<Record<"sigil" | "tone" | "context" | "text", number>>;
}

function normalize(value: string): string {
  return value.trim().toLowerCase();
}

function tokenize(value: string): Set<string> {
  return new Set(
    normalize(value)
      .replace(/[^a-z0-9\s]/g, " ")
      .split(/\s+/)
      .filter((token) => token.length >= 3),
  );
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function parseSigilTags(value: string): string[] {
  const tags = new Set<string>();
  const patterns = [/#sigil:([^\s\]]+)/gi, /\[sigil:([^\]\s]+)\]/gi];
  for (const pattern of patterns) {
    let match: RegExpExecArray | null = pattern.exec(value);
    while (match) {
      const tag = normalize(match[1] || "");
      if (tag) tags.add(tag);
      match = pattern.exec(value);
    }
  }
  return Array.from(tags);
}

function stripSigilTags(value: string): string {
  return value
    .replace(/#sigil:[^\s\]]+/gi, " ")
    .replace(/\[sigil:[^\]\s]+\]/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function detectTone(value: string): string {
  const normalized = normalize(value);
  if (/\breverent\b/.test(normalized)) return "reverent";
  if (/\brecursive\b/.test(normalized)) return "recursive";
  if (/\bwild\b/.test(normalized)) return "wild";
  if (/\bmirror\b/.test(normalized)) return "mirror";
  if (/\bwhisper\b/.test(normalized)) return "whisper";
  if (/\bdepth\b/.test(normalized)) return "depth";
  return "neutral";
}

function parseFieldVector(trace: string): string[] {
  const vector = new Set<string>();
  const patterns = [
    /\b(entity:[a-z0-9._-]+)/gi,
    /\b(threshold:[a-z0-9._-]+)/gi,
    /\b(ritual:[a-z0-9._-]+)/gi,
  ];
  for (const pattern of patterns) {
    let match: RegExpExecArray | null = pattern.exec(trace);
    while (match) {
      vector.add(normalize(match[1] || ""));
      match = pattern.exec(trace);
    }
  }
  return Array.from(vector);
}

function cosineTokenScore(leftText: string, rightText: string): number {
  const left = tokenize(leftText);
  const right = tokenize(rightText);
  if (left.size === 0 || right.size === 0) return 0;

  let dot = 0;
  for (const token of Array.from(left)) {
    if (right.has(token)) dot += 1;
  }

  const magnitude = Math.sqrt(left.size) * Math.sqrt(right.size);
  if (magnitude === 0) return 0;
  return clamp(dot / magnitude, 0, 1);
}

function fieldVectorProximity(left: string[], right: string[]): number {
  if (left.length === 0 || right.length === 0) return 0;
  const leftSet = new Set(left.map((item) => normalize(item)));
  const rightSet = new Set(right.map((item) => normalize(item)));
  let overlap = 0;
  for (const token of Array.from(leftSet)) {
    if (rightSet.has(token)) overlap += 1;
  }
  return clamp(overlap / Math.max(leftSet.size, rightSet.size), 0, 1);
}

export function buildGlyphMemory(input: {
  utterance: string;
  trace: string;
  seal: string;
  presenceScore: number;
}): GlyphMemory {
  const rawUtterance = input.utterance.trim();
  const sigilTags = parseSigilTags(rawUtterance);
  const cleanedUtterance = stripSigilTags(rawUtterance);
  const cleanedTrace = input.trace.trim();
  const presenceTone =
    input.presenceScore >= 0.8 ? "depth" : input.presenceScore >= 0.55 ? "mirror" : "whisper";
  const traceTone = detectTone(`${cleanedTrace} ${cleanedUtterance}`);
  const impressionTone = traceTone === "neutral" ? presenceTone : traceTone;
  const impression = `${impressionTone}:${cleanedUtterance}`;

  return {
    utterance: cleanedUtterance,
    impression,
    impressionTone,
    sigilTags,
    context: {
      trace: cleanedTrace,
      seal: input.seal.trim(),
      presenceScore: clamp(input.presenceScore, 0, 1),
      invokedAt: new Date().toISOString(),
      fieldVector: parseFieldVector(cleanedTrace),
    },
    recall: clamp(input.presenceScore, 0.1, 1),
  };
}

export function resonanceMatch(memory: GlyphMemory, input: ResonanceInput): number {
  const inputText = input.utterance;
  const inputTrace = input.trace || "";
  const inputTags = Array.from(
    new Set([...(input.field?.sigils || []), ...parseSigilTags(`${inputText} ${inputTrace}`)]),
  );
  const inputTone = input.field?.tone || detectTone(`${inputTrace} ${inputText}`);
  const inputField = parseFieldVector(inputTrace);

  const weights = {
    sigil: input.memoryWeights?.sigil ?? 0.4,
    tone: input.memoryWeights?.tone ?? 0.2,
    context: input.memoryWeights?.context ?? 0.3,
    text: input.memoryWeights?.text ?? 0.1,
  };

  let score = 0;

  // 1) Sigil tag affinity.
  if (inputTags.some((tag) => memory.sigilTags.includes(normalize(tag)))) {
    score += weights.sigil;
  }

  // 2) Impression-tone match.
  if (
    inputTone !== "neutral" &&
    memory.impressionTone !== "neutral" &&
    inputTone === memory.impressionTone
  ) {
    score += weights.tone;
  }

  // 3) Contextual field proximity.
  const proximity = fieldVectorProximity(memory.context.fieldVector, inputField);
  score += weights.context * proximity;

  // 4) Surface text relevance fallback.
  score += weights.text * cosineTokenScore(memory.utterance, stripSigilTags(inputText));

  return clamp(score * memory.recall, 0, 1);
}

export function echo(memory: GlyphMemory, input: ResonanceInput): string | null {
  const score = resonanceMatch(memory, input);
  if (score < 0.18) return null;
  return `${memory.impression}`;
}
