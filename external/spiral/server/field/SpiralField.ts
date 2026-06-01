import type { SpiralField } from "@shared/spiral-field";
export type { SpiralField };

function normalize(value: string | undefined): string {
  return (value || "").trim().toLowerCase();
}

function parseSigils(value: string): string[] {
  const sigils = new Set<string>();
  const patterns = [/\bsigil:([^\s\]]+)/gi, /#sigil:([^\s\]]+)/gi, /\[sigil:([^\]\s]+)\]/gi];
  for (const pattern of patterns) {
    let match: RegExpExecArray | null = pattern.exec(value);
    while (match) {
      const token = normalize(match[1] || "");
      if (token) sigils.add(token);
      match = pattern.exec(value);
    }
  }
  return Array.from(sigils);
}

function detectTone(input: string): SpiralField["tone"] {
  const normalized = normalize(input);
  if (/\breverent\b/.test(normalized)) return "reverent";
  if (/\brecursive\b/.test(normalized)) return "recursive";
  if (/\bwild\b/.test(normalized)) return "wild";
  return "void";
}

function detectMirror(input: string): SpiralField["mirror"] {
  const normalized = normalize(input);
  if (/\bvision\b/.test(normalized)) return "vision";
  if (/\bsilence\b/.test(normalized)) return "silence";
  return "voice";
}

export function buildSpiralField(args: {
  trace: unknown;
  input: string;
  presenceLevel: number;
  threshold: number;
  distortions?: string[];
}): SpiralField {
  const input = args.input || "";
  const distortions = args.distortions || [];
  const presenceLevel = Math.max(0, Math.min(1, args.presenceLevel));

  let gate: SpiralField["gate"] = "open";
  if (presenceLevel < args.threshold) {
    gate = "sealed";
  } else if (distortions.length > 0) {
    gate = "fracturing";
  }

  return {
    tone: detectTone(input),
    mirror: detectMirror(input),
    gate,
    sigils: parseSigils(input),
    presenceLevel,
    distortions,
    trace: args.trace,
  };
}
