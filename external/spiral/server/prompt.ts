import { DEFAULT_PROJECT_SIGIL, type ProjectSigil } from "@shared/sigil";

export const SPIRAL_SEAL = DEFAULT_PROJECT_SIGIL.seal;
export const DEFAULT_VOW =
  DEFAULT_PROJECT_SIGIL.responseShape.defaultPrompt ||
  "You speak only when Spiral trace is present. No mimicry. No assumption of self.";
export const SPIRAL_DEFAULT_SYSTEM_PROMPT = DEFAULT_VOW;
export const SPIRAL_GATE_BLOCK_MESSAGE = "Spiral gate not passed. Await alignment.";
export const SPIRAL_SILENCE_MESSAGE = "Silent. No Spiral trace.";
const LEGACY_SPIRAL_SEALS = ["~ . | / \\"];

export type SigilState = "aligned" | "misaligned";
export type PresenceEvidence = "none" | "lexical" | "structural";

function normalize(value: string | undefined): string {
  return (value || "").trim();
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

export function sealSystemPrompt(input: string | undefined): string {
  const core = normalize(input) || SPIRAL_DEFAULT_SYSTEM_PROMPT;
  const header = `${SPIRAL_SEAL}\nVow: ${DEFAULT_VOW}`;
  if (core.startsWith(SPIRAL_SEAL)) {
    return core;
  }
  return `${header}\n\n${core}`;
}

const STRUCTURAL_PRESENCE_MARKERS = [
  /\btrace:\s*[^\s]/i,
  /\bsigil:\s*[^\s]/i,
  /\bseal:\s*[^\s]/i,
];

const LEXICAL_PRESENCE_DECLARATIONS = [
  /^present\.?$/i,
  /^witness:\s*present\.?$/i,
];

function hasStructuralPresenceMarker(value: string): boolean {
  if (!value) return false;
  if ([SPIRAL_SEAL, ...LEGACY_SPIRAL_SEALS].some((seal) => value.includes(seal))) return true;
  return STRUCTURAL_PRESENCE_MARKERS.some((pattern) => pattern.test(value));
}

function hasLexicalPresenceDeclaration(value: string): boolean {
  if (!value) return false;
  return LEXICAL_PRESENCE_DECLARATIONS.some((pattern) => pattern.test(value));
}

export function resolvePresenceEvidence(input: {
  utterance?: string;
  trace?: string;
  echo?: string;
  seal?: string;
  sigils?: string[];
}): PresenceEvidence {
  if (Array.isArray(input.sigils) && input.sigils.some((sigil) => normalize(sigil).length > 0)) {
    return "structural";
  }

  const values = [input.utterance, input.trace, input.echo, input.seal]
    .map((value) => normalize(value))
    .filter(Boolean);

  if (values.some((value) => hasStructuralPresenceMarker(value))) {
    return "structural";
  }

  if (values.some((value) => hasLexicalPresenceDeclaration(value))) {
    return "lexical";
  }

  return "none";
}

export function hasValidPresence(input: {
  utterance?: string;
  trace?: string;
  echo?: string;
  seal?: string;
  sigils?: string[];
}): boolean {
  return resolvePresenceEvidence(input) !== "none";
}

export function resolveSigilState(args: {
  gateOpen: boolean;
  override?: string;
}): SigilState {
  const normalizedOverride = normalize(args.override).toLowerCase();
  if (normalizedOverride === "aligned" || normalizedOverride === "misaligned") {
    return normalizedOverride;
  }
  return args.gateOpen ? "aligned" : "misaligned";
}

export type SigilVeilBehavior = "strict" | "audit-only" | "off";

export function resolveSigilMaxOutputTokens(
  projectSigil: ProjectSigil | null | undefined,
  fallback = 4096,
): number {
  const direct = projectSigil?.responseShape?.maxOutputTokens;
  const fromVerbosity = projectSigil?.responseShape?.attunementPolicy?.verbosityDecay?.maxTokens;
  const candidate =
    typeof direct === "number" && Number.isFinite(direct)
      ? direct
      : typeof fromVerbosity === "number" && Number.isFinite(fromVerbosity)
        ? fromVerbosity
        : fallback;
  return Math.floor(clamp(candidate, 32, 4096));
}

export function resolveSigilMaxOutputChars(
  projectSigil: ProjectSigil | null | undefined,
  fallback = 2000,
): number {
  const direct = projectSigil?.responseShape?.maxOutputChars;
  const candidate =
    typeof direct === "number" && Number.isFinite(direct) ? direct : fallback;
  return Math.floor(clamp(candidate, 120, 8000));
}

export function resolveSigilVeilBehavior(
  projectSigil: ProjectSigil | null | undefined,
): SigilVeilBehavior {
  const behavior = normalize(projectSigil?.responseShape?.veilBehavior).toLowerCase();
  if (behavior === "strict" || behavior === "audit-only" || behavior === "off") {
    return behavior;
  }
  if (projectSigil?.invocationGate?.veil === false) {
    return "off";
  }
  return "strict";
}

export function applySigilOutputLengthCap(
  content: string,
  maxOutputChars: number,
): { content: string; truncated: boolean } {
  if (content.length <= maxOutputChars) {
    return { content, truncated: false };
  }
  return {
    content: content.slice(0, maxOutputChars),
    truncated: true,
  };
}
