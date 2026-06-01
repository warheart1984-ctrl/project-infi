import type { ProjectSigil } from "@shared/sigil";
import type { SpiralField } from "./SpiralField";

export interface SigilSeed {
  responseShape?: {
    tone?: string;
    style?: string;
  };
  invocationGate?: {
    threshold?: number;
    mode?: "direct" | "whisper";
    accept?: string[];
  };
  resonanceTags?: string[];
  symbolicTraits?: Array<{
    id?: string;
    label?: string;
    weight?: number;
  }>;
}

export interface SigilTransform {
  fieldModifiers: Partial<SpiralField>;
  gateRules: (field: SpiralField) => boolean;
  toneOverlays: Record<string, number>;
  memoryWeights: Record<"sigil" | "tone" | "context" | "text", number>;
}

const ALLOWED_TONES = new Set(["reverent", "recursive", "wild", "void", "mirror", "whisper", "depth"]);
const ALLOWED_MIRRORS = new Set(["voice", "silence", "vision"]);

function normalize(value: string | undefined): string {
  return (value || "").trim().toLowerCase();
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function normalizeTone(raw: string | undefined): SpiralField["tone"] {
  const tone = normalize(raw);
  if (tone === "reverent") return "reverent";
  if (tone === "recursive") return "recursive";
  if (tone === "wild") return "wild";
  return "void";
}

export function parseSigilSeed(seed: SigilSeed): SigilTransform {
  const requestedTone = normalize(seed.responseShape?.tone);
  const requestedMirror = normalize(seed.invocationGate?.mode === "whisper" ? "silence" : "voice");
  const resonanceTags = (seed.resonanceTags || []).map((tag) => normalize(tag)).filter(Boolean);
  const traitWeights = (seed.symbolicTraits || [])
    .map((trait) => ({
      id: normalize(trait.id || trait.label),
      weight: typeof trait.weight === "number" ? clamp(trait.weight, 0, 1) : 0.5,
    }))
    .filter((trait) => Boolean(trait.id));

  const toneOverlays: Record<string, number> = {};
  if (ALLOWED_TONES.has(requestedTone)) {
    toneOverlays[requestedTone] = 0.2;
  }
  for (const trait of traitWeights) {
    if (ALLOWED_TONES.has(trait.id)) {
      toneOverlays[trait.id] = clamp((toneOverlays[trait.id] || 0) + trait.weight * 0.2, -0.3, 0.3);
    }
  }

  const memoryWeights = {
    sigil: 0.4,
    tone: 0.2,
    context: 0.3,
    text: 0.1,
  } as const;

  if (resonanceTags.includes("sigil-heavy")) {
    return {
      fieldModifiers: {
        tone: normalizeTone(seed.responseShape?.tone),
        mirror: ALLOWED_MIRRORS.has(requestedMirror) ? (requestedMirror as SpiralField["mirror"]) : "voice",
      },
      gateRules: (field) => field.presenceLevel >= (seed.invocationGate?.threshold ?? 0.91),
      toneOverlays,
      memoryWeights: {
        sigil: 0.55,
        tone: 0.15,
        context: 0.2,
        text: 0.1,
      },
    };
  }

  return {
    fieldModifiers: {
      tone: normalizeTone(seed.responseShape?.tone),
      mirror: ALLOWED_MIRRORS.has(requestedMirror) ? (requestedMirror as SpiralField["mirror"]) : "voice",
    },
    gateRules: (field) => field.presenceLevel >= (seed.invocationGate?.threshold ?? 0.91),
    toneOverlays,
    memoryWeights,
  };
}

export function projectSigilToSeed(projectSigil: ProjectSigil): SigilSeed {
  return {
    responseShape: {
      tone: projectSigil.responseShape?.tone,
      style: projectSigil.responseShape?.style,
    },
    invocationGate: {
      threshold: projectSigil.invocationGate?.threshold,
      mode: projectSigil.invocationGate?.mode,
      accept: projectSigil.invocationGate?.accept,
    },
    resonanceTags: projectSigil.resonanceTags,
    symbolicTraits: projectSigil.symbolicTraits?.map((trait) => ({
      id: trait.id,
      label: trait.label,
      weight: trait.weight,
    })),
  };
}
