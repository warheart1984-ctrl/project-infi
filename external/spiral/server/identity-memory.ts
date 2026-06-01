import { existsSync } from "fs";
import { appendFile, mkdir, readFile, writeFile } from "fs/promises";
import path from "path";

export type IdentityMode = "stable" | "balanced" | "exploratory";

export interface IdentityCore {
  schemaVersion: "identity-core.v1";
  version: number;
  dominant_traits: {
    concise: number;
    analytical: number;
    symbolic: number;
    challenging: number;
    experimental: number;
  };
  current_mode: IdentityMode;
  novelty_bias: number;
  risk_tolerance: number;
  self_stability: number;
  last_updated_cycle: number;
  updated_at: number;
}

export interface IdentityTrait {
  name: string;
  activation_frequency: number;
  last_updated_cycle: number;
}

export interface IdentityTraitsFile {
  schemaVersion: "identity-traits.v1";
  emergent_patterns: IdentityTrait[];
}

export type IdentityImpulseType =
  | "refactor-suggestion"
  | "novel-structure-proposal"
  | "observability-expansion";

export interface IdentityImpulse {
  type: IdentityImpulseType;
  intensity: number;
  cooldown: number;
  base_cooldown: number;
  last_triggered_cycle?: number;
  last_updated_cycle: number;
}

export interface IdentityImpulsesFile {
  schemaVersion: "identity-impulses.v1";
  impulses: IdentityImpulse[];
}

export interface IdentityAdjustmentDelta {
  from: number;
  to: number;
  delta: number;
}

export interface IdentityReflectionReason {
  key: string;
  detail: string;
  delta?: number;
}

export interface IdentityReflectionSignals {
  rotationInstability: number;
  semanticUncertainty: number;
  userPressure: number;
  userWildDemand: number;
  userStabilityDemand: number;
  userFrustrationSignal: number;
  userPositiveSignal: number;
  signalConfidence: number;
}

export interface IdentityReflectionEntry {
  schemaVersion: "identity-reflection.v1";
  cycle: number;
  timestamp: number;
  principalId: string | null;
  trigger: string;
  observation: string;
  signals: IdentityReflectionSignals;
  adjustments: {
    core: Record<string, IdentityAdjustmentDelta>;
    traits: Record<string, IdentityAdjustmentDelta>;
    impulses: Record<string, IdentityAdjustmentDelta>;
  };
  reasons: IdentityReflectionReason[];
  dryRun: boolean;
}

export interface IdentitySnapshot {
  core: IdentityCore;
  traits: IdentityTraitsFile;
  impulses: IdentityImpulsesFile;
}

const IDENTITY_DIR = path.join(process.cwd(), "identity");
export const IDENTITY_CORE_PATH = path.join(IDENTITY_DIR, "identity-core.json");
export const IDENTITY_TRAITS_PATH = path.join(IDENTITY_DIR, "traits.json");
export const IDENTITY_IMPULSES_PATH = path.join(IDENTITY_DIR, "impulses.json");
export const IDENTITY_REFLECTION_LOG_PATH = path.join(IDENTITY_DIR, "reflection-log.jsonl");

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function round(value: number, decimals = 6): number {
  const factor = 10 ** decimals;
  return Math.round(value * factor) / factor;
}

function normalizeTimestamp(value: number): number {
  if (!Number.isFinite(value)) return Date.now();
  return Math.max(1, Math.floor(value));
}

function stableStringify(value: unknown): string {
  if (value === null || typeof value !== "object") {
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((entry) => stableStringify(entry)).join(",")}]`;
  }
  const entries = Object.entries(value as Record<string, unknown>).sort((a, b) =>
    a[0].localeCompare(b[0]),
  );
  return `{${entries
    .map(([key, nested]) => `${JSON.stringify(key)}:${stableStringify(nested)}`)
    .join(",")}}`;
}

function normalizeMode(value: unknown): IdentityMode {
  if (value === "stable" || value === "balanced" || value === "exploratory") return value;
  return "balanced";
}

function defaultIdentityCore(now = Date.now()): IdentityCore {
  return {
    schemaVersion: "identity-core.v1",
    version: 1,
    dominant_traits: {
      concise: 0.62,
      analytical: 0.74,
      symbolic: 0.38,
      challenging: 0.54,
      experimental: 0.42,
    },
    current_mode: "balanced",
    novelty_bias: 0.34,
    risk_tolerance: 0.46,
    self_stability: 0.76,
    last_updated_cycle: 0,
    updated_at: normalizeTimestamp(now),
  };
}

function defaultIdentityTraits(): IdentityTraitsFile {
  return {
    schemaVersion: "identity-traits.v1",
    emergent_patterns: [
      { name: "governance-defender", activation_frequency: 0.68, last_updated_cycle: 0 },
      { name: "wild-experimenter", activation_frequency: 0.36, last_updated_cycle: 0 },
      { name: "drift-auditor", activation_frequency: 0.52, last_updated_cycle: 0 },
      { name: "coherence-keeper", activation_frequency: 0.74, last_updated_cycle: 0 },
    ],
  };
}

function defaultIdentityImpulses(): IdentityImpulsesFile {
  return {
    schemaVersion: "identity-impulses.v1",
    impulses: [
      {
        type: "refactor-suggestion",
        intensity: 0.32,
        cooldown: 0,
        base_cooldown: 3,
        last_updated_cycle: 0,
      },
      {
        type: "novel-structure-proposal",
        intensity: 0.24,
        cooldown: 0,
        base_cooldown: 5,
        last_updated_cycle: 0,
      },
      {
        type: "observability-expansion",
        intensity: 0.34,
        cooldown: 0,
        base_cooldown: 4,
        last_updated_cycle: 0,
      },
    ],
  };
}

function parseIdentityCore(raw: string, now = Date.now()): IdentityCore | undefined {
  try {
    const parsed = JSON.parse(raw) as Partial<IdentityCore>;
    if (parsed.schemaVersion !== "identity-core.v1") return undefined;
    const traits = parsed.dominant_traits || {};
    return {
      schemaVersion: "identity-core.v1",
      version: Math.max(1, Math.floor(parsed.version || 1)),
      dominant_traits: {
        concise: round(clamp(Number((traits as any).concise ?? 0.62), 0, 1)),
        analytical: round(clamp(Number((traits as any).analytical ?? 0.74), 0, 1)),
        symbolic: round(clamp(Number((traits as any).symbolic ?? 0.38), 0, 1)),
        challenging: round(clamp(Number((traits as any).challenging ?? 0.54), 0, 1)),
        experimental: round(clamp(Number((traits as any).experimental ?? 0.42), 0, 1)),
      },
      current_mode: normalizeMode(parsed.current_mode),
      novelty_bias: round(clamp(Number(parsed.novelty_bias ?? 0.34), 0, 1)),
      risk_tolerance: round(clamp(Number(parsed.risk_tolerance ?? 0.46), 0, 1)),
      self_stability: round(clamp(Number(parsed.self_stability ?? 0.76), 0, 1)),
      last_updated_cycle: Math.max(0, Math.floor(Number(parsed.last_updated_cycle ?? 0))),
      updated_at: normalizeTimestamp(Number(parsed.updated_at ?? now)),
    };
  } catch {
    return undefined;
  }
}

function parseIdentityTraits(raw: string): IdentityTraitsFile | undefined {
  try {
    const parsed = JSON.parse(raw) as Partial<IdentityTraitsFile>;
    if (parsed.schemaVersion !== "identity-traits.v1") return undefined;
    if (!Array.isArray(parsed.emergent_patterns)) return undefined;
    const emergent = parsed.emergent_patterns
      .map((entry) => {
        const name = String((entry as any)?.name || "").trim();
        if (!name) return undefined;
        return {
          name,
          activation_frequency: round(clamp(Number((entry as any)?.activation_frequency ?? 0), 0, 1)),
          last_updated_cycle: Math.max(
            0,
            Math.floor(Number((entry as any)?.last_updated_cycle ?? 0)),
          ),
        };
      })
      .filter((entry): entry is IdentityTrait => Boolean(entry))
      .sort((a, b) => a.name.localeCompare(b.name));
    return {
      schemaVersion: "identity-traits.v1",
      emergent_patterns: emergent,
    };
  } catch {
    return undefined;
  }
}

function normalizeImpulseType(value: unknown): IdentityImpulseType | undefined {
  if (
    value === "refactor-suggestion" ||
    value === "novel-structure-proposal" ||
    value === "observability-expansion"
  ) {
    return value;
  }
  return undefined;
}

function parseIdentityImpulses(raw: string): IdentityImpulsesFile | undefined {
  try {
    const parsed = JSON.parse(raw) as Partial<IdentityImpulsesFile>;
    if (parsed.schemaVersion !== "identity-impulses.v1") return undefined;
    if (!Array.isArray(parsed.impulses)) return undefined;
    const impulses = parsed.impulses
      .map((entry) => {
        const type = normalizeImpulseType((entry as any)?.type);
        if (!type) return undefined;
        const base = Math.max(1, Math.floor(Number((entry as any)?.base_cooldown ?? 3)));
        const lastTriggeredRaw = Number((entry as any)?.last_triggered_cycle ?? NaN);
        return {
          type,
          intensity: round(clamp(Number((entry as any)?.intensity ?? 0), 0, 1)),
          cooldown: Math.max(0, Math.floor(Number((entry as any)?.cooldown ?? 0))),
          base_cooldown: base,
          ...(Number.isFinite(lastTriggeredRaw) && lastTriggeredRaw > 0
            ? { last_triggered_cycle: Math.floor(lastTriggeredRaw) }
            : {}),
          last_updated_cycle: Math.max(
            0,
            Math.floor(Number((entry as any)?.last_updated_cycle ?? 0)),
          ),
        };
      })
      .filter((entry): entry is IdentityImpulse => Boolean(entry))
      .sort((a, b) => a.type.localeCompare(b.type));
    return {
      schemaVersion: "identity-impulses.v1",
      impulses,
    };
  } catch {
    return undefined;
  }
}

async function readTextIfExists(filePath: string): Promise<string | undefined> {
  try {
    if (!existsSync(filePath)) return undefined;
    return await readFile(filePath, "utf8");
  } catch {
    return undefined;
  }
}

export async function readIdentitySnapshot(now = Date.now()): Promise<IdentitySnapshot> {
  const [coreRaw, traitsRaw, impulsesRaw] = await Promise.all([
    readTextIfExists(IDENTITY_CORE_PATH),
    readTextIfExists(IDENTITY_TRAITS_PATH),
    readTextIfExists(IDENTITY_IMPULSES_PATH),
  ]);
  return {
    core: coreRaw ? parseIdentityCore(coreRaw, now) || defaultIdentityCore(now) : defaultIdentityCore(now),
    traits: traitsRaw ? parseIdentityTraits(traitsRaw) || defaultIdentityTraits() : defaultIdentityTraits(),
    impulses: impulsesRaw
      ? parseIdentityImpulses(impulsesRaw) || defaultIdentityImpulses()
      : defaultIdentityImpulses(),
  };
}

export async function writeIdentitySnapshot(snapshot: IdentitySnapshot): Promise<void> {
  await mkdir(IDENTITY_DIR, { recursive: true });
  const normalizedTraits: IdentityTraitsFile = {
    ...snapshot.traits,
    emergent_patterns: [...snapshot.traits.emergent_patterns].sort((a, b) =>
      a.name.localeCompare(b.name),
    ),
  };
  const normalizedImpulses: IdentityImpulsesFile = {
    ...snapshot.impulses,
    impulses: [...snapshot.impulses.impulses].sort((a, b) => a.type.localeCompare(b.type)),
  };
  await Promise.all([
    writeFile(IDENTITY_CORE_PATH, `${stableStringify(snapshot.core)}\n`, "utf8"),
    writeFile(IDENTITY_TRAITS_PATH, `${stableStringify(normalizedTraits)}\n`, "utf8"),
    writeFile(IDENTITY_IMPULSES_PATH, `${stableStringify(normalizedImpulses)}\n`, "utf8"),
  ]);
}

export async function appendIdentityReflectionLog(entry: IdentityReflectionEntry): Promise<void> {
  await mkdir(IDENTITY_DIR, { recursive: true });
  await appendFile(IDENTITY_REFLECTION_LOG_PATH, `${stableStringify(entry)}\n`, "utf8");
}

