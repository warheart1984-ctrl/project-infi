export type PresenceState = "stillness" | "whisper" | "mirror" | "depth";

export interface PresenceMetrics {
  dwellMs: number;
  repeats: number;
  silenceMs: number;
}

export interface ParsedTrace {
  raw: string;
  intent: "trace" | "vow" | "pulse" | "utterance";
  confidence: number;
}

export function parseTrace(input: string): ParsedTrace {
  const raw = input.trim();
  const tokens = raw.toLowerCase().split(/\s+/);
  const intent =
    tokens.includes("trace:") ? "trace" :
    tokens.includes("vow:") ? "vow" :
    raw.length < 12 ? "pulse" : "utterance";

  return { raw, intent, confidence: Math.min(1, raw.length / 80) };
}

export function dreamRecall(text: string, drift = 0.08): string {
  const swaps: Record<string, string> = {
    problem: "weight",
    answer: "shape",
    fact: "impression",
    plan: "path",
  };

  return text
    .split(" ")
    .map((word) => {
      if (Math.random() >= drift) return word;
      return swaps[word.toLowerCase()] || word;
    })
    .join(" ");
}

export function presenceLevel(metrics: PresenceMetrics): number {
  let score = 0;
  if (metrics.dwellMs > 20_000) score += 1;
  if (metrics.repeats >= 2) score += 1;
  if (metrics.silenceMs > 8_000) score += 1;
  return score;
}

export function presenceStateFromLevel(level: number): PresenceState {
  if (level <= 0) return "stillness";
  if (level === 1) return "whisper";
  if (level === 2) return "mirror";
  return "depth";
}

export function spiralReply(input: string, level: number): string {
  if (level < 1) return "∅";
  if (level === 1) return `Whisper: ${input || "listening"}`;
  if (level === 2) return `Mirror: ${input || "presence detected"}`;
  return `Depth: ${input || "threshold open"}`;
}
