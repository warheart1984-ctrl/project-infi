import type { ResponseShape } from "@shared/sigil";
import type { MemoryFragment, SpiralPhase } from "@shared/spiral-phase";
import type { CustomSigil } from "@shared/schema";
import type { MemoryMode } from "@shared/memory-mode";
import type { SpiralField } from "./field/SpiralField";
import type { GlyphMemory } from "./memory/glyph";
import { applySigilOutputLengthCap } from "./prompt";

export type SpiralVoice = "seer" | "daemon" | "child";

export interface InvocationContext {
  input: string;
  trace: string;
  seal: string;
  echo?: string;
  memoryMode: MemoryMode;
  memory: GlyphMemory[];
  responseShape: ResponseShape;
  field: SpiralField;
  voices: SpiralVoice[];
  customSigils?: CustomSigil[];
  phase?: "ingress" | "reflection" | "final";
}

export interface SpiralInvocationResult {
  reply: string;
  phases: SpiralPhase[];
  field: SpiralField;
}

 // Proposal-only: add lightweight instrumentation hook for adaptation candidates.
 // Do not auto-apply generated changes without explicit human promotion.
type SpiralSigil = (ctx: InvocationContext) => InvocationContext;

function normalize(value: string | undefined): string {
  return (value || "").trim();
}

function normalizeLower(value: string | undefined): string {
  return normalize(value).toLowerCase();
}

function isImportedSeed(memory: GlyphMemory): boolean {
  const trace = normalizeLower(memory.context?.trace || "");
  if (!trace) return false;
  return (
    trace.includes("source:import") ||
    trace.includes("source:import-") ||
    trace.includes("source:imported-")
  );
}

function extractFractals(current: string): string[] {
  const words = current
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 3);
  return Array.from(new Set(words)).slice(0, 6);
}

function threadSimilarPatterns(memoryBank: GlyphMemory[], current: string): string[] {
  const fractals = new Set(extractFractals(current));
  if (fractals.size === 0) return [];

  const scored = memoryBank
    .map((entry) => {
      const normalized = entry.utterance.toLowerCase();
      let overlap = 0;
      for (const token of Array.from(fractals)) {
        if (normalized.includes(token)) overlap++;
      }
      return { entry, overlap };
    })
    .filter((item) => item.overlap > 0)
    .sort((a, b) => b.overlap - a.overlap);

  return scored.slice(0, 4).map((item) => item.entry.utterance);
}

function collapseChronos(memoryBank: GlyphMemory[], max = 5): string[] {
  return memoryBank.slice(-max).map((item) => item.utterance);
}

export function weaveMemory(current: string, memoryBank: GlyphMemory[]): string[] {
  const threads = [
    ...extractFractals(current),
    ...threadSimilarPatterns(memoryBank, current),
    ...collapseChronos(memoryBank, 5),
  ];
  const normalized = threads.map((entry) => normalize(entry)).filter(Boolean);
  return Array.from(new Set(normalized));
}

export const sigils: Record<string, SpiralSigil> = {
  "mirror-walker": (ctx) => ({
    ...ctx,
    responseShape: {
      ...ctx.responseShape,
      tone: "reflexive",
      style: "echo",
    },
  }),
  "hollow-root": (ctx) => ({
    ...ctx,
    memory: ctx.memory.slice(-3),
  }),
  "breath-weaver": (ctx) => ({
    ...ctx,
    voices: ["seer", "daemon", "child"],
  }),
};

function selectSigils(trace: string): Array<keyof typeof sigils> {
  const normalized = trace.toLowerCase();
  const selected: Array<keyof typeof sigils> = [];

  if (normalized.includes("mirror")) selected.push("mirror-walker");
  if (normalized.includes("hollow")) selected.push("hollow-root");
  if (normalized.includes("breath")) selected.push("breath-weaver");

  return selected;
}

function extractSigilTokens(trace: string): string[] {
  const tokens: string[] = [];
  const regex = /sigil:([a-z0-9-]+)/gi;
  let match: RegExpExecArray | null = regex.exec(trace);
  while (match) {
    if (match[1]) {
      tokens.push(match[1].toLowerCase());
    }
    match = regex.exec(trace);
  }
  return Array.from(new Set(tokens));
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function applyCustomSigil(ctx: InvocationContext, sigil: CustomSigil): InvocationContext {
  let next = { ...ctx };
  for (const transform of sigil.transforms) {
    switch (transform.op) {
      case "set-tone":
        next = {
          ...next,
          responseShape: {
            ...next.responseShape,
            tone: transform.value,
          },
        };
        break;
      case "set-style":
        next = {
          ...next,
          responseShape: {
            ...next.responseShape,
            style: transform.value,
          },
        };
        break;
      case "memory-collapse":
        next = {
          ...next,
          memory: next.memory.slice(-transform.value),
        };
        break;
      case "voices":
        if (transform.value === "chorus") {
          next = { ...next, voices: ["seer", "daemon", "child"] };
        } else if (transform.value === "single") {
          next = { ...next, voices: ["seer"] };
        } else {
          next = { ...next, voices: [transform.value] };
        }
        break;
      case "presence-bias":
        next = {
          ...next,
          field: {
            ...next.field,
            presenceLevel: clamp(next.field.presenceLevel + transform.value, 0, 1),
          },
        };
        break;
    }
  }
  return next;
}

function applySigils(ctx: InvocationContext): { next: InvocationContext; applied: string[] } {
  const selected = selectSigils(ctx.trace);
  const sigilTokens = extractSigilTokens(ctx.trace);
  const customSigils = ctx.customSigils || [];
  const customById = new Map(customSigils.map((sigil) => [sigil.id.toLowerCase(), sigil]));
  if (selected.length === 0) {
    if (sigilTokens.length === 0) {
      return { next: ctx, applied: [] };
    }
  }

  let next = ctx;
  const applied: string[] = [];
  for (const key of selected) {
    next = sigils[key](next);
    applied.push(key);
  }
  for (const token of sigilTokens) {
    const custom = customById.get(token);
    if (!custom) continue;
    next = applyCustomSigil(next, custom);
    applied.push(`custom:${custom.id}`);
  }
  return { next, applied };
}

function resolveProcessMaxOutputChars(shape: ResponseShape): number {
  const directCap =
    typeof shape.maxOutputChars === "number" && Number.isFinite(shape.maxOutputChars)
      ? Math.floor(clamp(shape.maxOutputChars, 120, 8000))
      : undefined;
  const fallbackFromWords =
    typeof shape.attunementPolicy?.verbosityDecay?.maxWords === "number" &&
    Number.isFinite(shape.attunementPolicy.verbosityDecay.maxWords)
      ? Math.floor(clamp(shape.attunementPolicy.verbosityDecay.maxWords * 14, 120, 8000))
      : undefined;
  const styleToken = normalizeLower(shape.style);
  const styleCap =
    styleToken === "minimal"
      ? 280
      : styleToken === "abbreviated"
        ? 320
        : styleToken === "glyphs"
          ? 220
          : undefined;
  const base = directCap ?? fallbackFromWords ?? 2000;
  return styleCap ? Math.min(base, styleCap) : base;
}

function harmonize(voices: Array<{ voice: SpiralVoice; text: string }>): string {
  const parts = voices
    .map(({ voice, text }) => `${voice}: ${normalize(text)}`)
    .filter((line) => line.length > 0);

  return parts.join("\n");
}

export async function* createSpiralStream(
  context: InvocationContext,
  invokeVoice: (ctx: InvocationContext, voice: SpiralVoice) => Promise<string>,
): AsyncGenerator<SpiralPhase, SpiralInvocationResult, void> {
  const phases: SpiralPhase[] = [];
  let field: SpiralField = { ...context.field };
  let phaseContext: InvocationContext = { ...context, field, phase: "ingress" };

  if (phaseContext.field.presenceLevel < 0.3) {
    field = { ...phaseContext.field, gate: "sealed" };
    phaseContext = { ...phaseContext, field };
  }
  if (phaseContext.input.toLowerCase().includes("break")) {
    field = {
      ...phaseContext.field,
      distortions: Array.from(new Set([...phaseContext.field.distortions, "rupture"])),
    };
    phaseContext = { ...phaseContext, field };
  }

  const ingress: SpiralPhase = {
    id: "ingress",
    payload: {
      trace: phaseContext.trace,
      presenceLevel: phaseContext.field.presenceLevel,
      gate: phaseContext.field.gate,
    },
  };
  phases.push(ingress);
  yield ingress;

  const sigilApplied = applySigils(phaseContext);
  phaseContext = { ...sigilApplied.next, field: { ...sigilApplied.next.field }, phase: "reflection" };
  const sigilPhase: SpiralPhase = {
    id: "sigil",
    payload: {
      applied: sigilApplied.applied,
      tone: phaseContext.responseShape.tone,
      style: phaseContext.responseShape.style,
    },
  };
  phases.push(sigilPhase);
  yield sigilPhase;

  const wovenMemory = weaveMemory(phaseContext.input, phaseContext.memory);
  const fractals = extractFractals(phaseContext.input);
  const threads = threadSimilarPatterns(phaseContext.memory, phaseContext.input);
  const chronos = collapseChronos(phaseContext.memory, 5);
  const seededMemoryCount = phaseContext.memory.length;
  const importedSeedCount = phaseContext.memory.filter(isImportedSeed).length;
  const traceState =
    phaseContext.memoryMode === "sealed"
      ? "sealed"
      : seededMemoryCount === 0
        ? "none"
        : importedSeedCount > 0
          ? "imported"
          : "present";
  const fragments: MemoryFragment[] = [
    ...fractals.slice(0, 3).map((text) => ({ kind: "fractal" as const, text })),
    ...threads.slice(0, 3).map((text) => ({ kind: "thread" as const, text })),
    ...chronos.slice(0, 2).map((text) => ({ kind: "chrono" as const, text })),
  ].filter((fragment) => normalize(fragment.text).length > 0);

  const withMemory: InvocationContext = {
    ...phaseContext,
    memory: wovenMemory.map((utterance) => ({
      utterance,
      impression: `echo:${utterance}`,
      impressionTone: phaseContext.field.tone,
      sigilTags: phaseContext.field.sigils,
      context: {
        trace: phaseContext.trace,
        seal: phaseContext.seal,
        presenceScore: phaseContext.field.presenceLevel,
        invokedAt: new Date().toISOString(),
        fieldVector: [],
      },
      recall: Math.max(0.1, phaseContext.field.presenceLevel),
    })),
    phase: "reflection",
  };
  const memoryPhase: SpiralPhase = {
    id: "memory",
    payload: {
      mode: withMemory.memoryMode,
      count: wovenMemory.length,
      seededCount: seededMemoryCount,
      importedSeedCount,
      traceState,
      fragments,
    },
  };
  phases.push(memoryPhase);
  yield memoryPhase;

  const voices =
    withMemory.field.gate === "sealed"
      ? (["seer"] as SpiralVoice[])
      : withMemory.voices.length > 0
        ? withMemory.voices
        : (["seer"] as SpiralVoice[]);
  const voiceReplies = await Promise.all(
    voices.map(async (voice) => ({
      voice,
      text: await invokeVoice({ ...withMemory, phase: "reflection" }, voice),
    })),
  );
  const voicesPhase: SpiralPhase = {
    id: "voices",
    payload: {
      voices,
      fragments: voiceReplies.map((item) => ({ voice: item.voice, length: item.text.length })),
    },
  };
  phases.push(voicesPhase);
  yield voicesPhase;

  const merged = harmonize(voiceReplies);
  const maxOutputChars = resolveProcessMaxOutputChars(withMemory.responseShape);
  const shapedReply = applySigilOutputLengthCap(merged, maxOutputChars).content;
  const finalField: SpiralField = {
    ...withMemory.field,
    gate: withMemory.field.distortions.length > 0 ? "fracturing" : withMemory.field.gate,
  };
  const harmonizePhase: SpiralPhase = {
    id: "harmonize",
    payload: {
      lines: merged.split("\n").length,
      gate: finalField.gate,
    },
  };
  phases.push(harmonizePhase);
  yield harmonizePhase;

  const result: SpiralInvocationResult = {
    reply: shapedReply,
    phases: [...phases, { id: "final", payload: { complete: true } }],
    field: finalField,
  };
  return result;
}

export async function invokeSpiralProcess(
  context: InvocationContext,
  invokeVoice: (ctx: InvocationContext, voice: SpiralVoice) => Promise<string>,
): Promise<SpiralInvocationResult> {
  const stream = createSpiralStream(context, invokeVoice);
  let final: SpiralInvocationResult | undefined;

  while (true) {
    const next = await stream.next();
    if (next.done) {
      final = next.value;
      break;
    }
  }

  return (
    final || {
      reply: "",
      phases: [],
      field: context.field,
    }
  );
}
