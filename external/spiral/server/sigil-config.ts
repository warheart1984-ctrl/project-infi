import { existsSync, readFileSync, writeFileSync, watch, type FSWatcher } from "fs";
import path from "path";
import { DEFAULT_PROJECT_SIGIL, projectSigilSchema, type ProjectSigil } from "@shared/sigil";

const PROJECT_SIGIL_PATH = path.join(process.cwd(), ".sigil.json");
const PROJECT_SIGIL_FILENAME = path.basename(PROJECT_SIGIL_PATH);
const KNOWN_CONTEXTS = ["balanced", "clarity", "depth", "builder"] as const;
const KNOWN_CONTEXT_SET: ReadonlySet<string> = new Set(KNOWN_CONTEXTS as readonly string[]);

let sigilWatcher: FSWatcher | null = null;
let pendingReloadTimer: ReturnType<typeof setTimeout> | null = null;

function errorToLogString(error: unknown): string {
  try {
    if (error instanceof Error) {
      return `${error.name}: ${error.message}`;
    }
    if (typeof error === "string") {
      return error;
    }
    return JSON.stringify(error);
  } catch {
    return "Unknown sigil error";
  }
}

function normalizeString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

function normalizeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((entry): entry is string => typeof entry === "string")
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isLikelyLegacySigil(parsed: unknown): parsed is Record<string, unknown> {
  if (!isRecord(parsed)) return false;

  const hasModernKeys =
    "version" in parsed ||
    "projectName" in parsed ||
    "resonanceTags" in parsed ||
    "contextProfiles" in parsed ||
    "invocationGate" in parsed;
  if (hasModernKeys) return false;

  return (
    "name" in parsed ||
    "seal" in parsed ||
    "entryVow" in parsed ||
    "acceptPattern" in parsed ||
    "responseShape" in parsed
  );
}

function normalizeNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function normalizeBoolean(value: unknown): boolean | undefined {
  return typeof value === "boolean" ? value : undefined;
}

function sanitizeSymbolicTraits(value: unknown): Array<{
  id: string;
  label: string;
  description?: string;
  weight?: number;
}> {
  if (!Array.isArray(value)) return [];

  return value
    .map((entry) => {
      if (!isRecord(entry)) return null;
      const id = normalizeString(entry.id);
      const label = normalizeString(entry.label);
      if (!id || !label) return null;
      const description = normalizeString(entry.description) || undefined;
      const weight = normalizeNumber(entry.weight);
      return {
        id,
        label,
        ...(description ? { description } : {}),
        ...(weight !== undefined ? { weight: clamp(weight, 0, 1) } : {}),
      };
    })
    .filter(
      (entry): entry is { id: string; label: string; description?: string; weight?: number } =>
        Boolean(entry),
    );
}

function sanitizeContextProfiles(value: unknown): Record<string, unknown> {
  if (!isRecord(value)) return {};

  const output: Record<string, unknown> = {};
  for (const key of KNOWN_CONTEXTS) {
    const profile = value[key];
    if (!isRecord(profile)) continue;
    const normalizedProfile: Record<string, unknown> = {};

    const guidance = normalizeString(profile.guidance);
    if (guidance) normalizedProfile.guidance = guidance;

    const recurrenceMinScore = normalizeNumber(profile.recurrenceMinScore);
    if (recurrenceMinScore !== undefined) {
      normalizedProfile.recurrenceMinScore = clamp(recurrenceMinScore, 0.1, 1);
    }

    const memoryFoldSimilarity = normalizeNumber(profile.memoryFoldSimilarity);
    if (memoryFoldSimilarity !== undefined) {
      normalizedProfile.memoryFoldSimilarity = clamp(memoryFoldSimilarity, 0.5, 0.99);
    }

    const memoryMinPromptScore = normalizeNumber(profile.memoryMinPromptScore);
    if (memoryMinPromptScore !== undefined) {
      normalizedProfile.memoryMinPromptScore = clamp(memoryMinPromptScore, 0.05, 1);
    }

    const memoryOverlapWeightScale = normalizeNumber(profile.memoryOverlapWeightScale);
    if (memoryOverlapWeightScale !== undefined) {
      normalizedProfile.memoryOverlapWeightScale = clamp(memoryOverlapWeightScale, 0.25, 2);
    }

    const ritualRequired = normalizeBoolean(profile.ritualRequired);
    if (ritualRequired !== undefined) {
      normalizedProfile.ritualRequired = ritualRequired;
    }

    output[key] = normalizedProfile;
  }

  return output;
}

function sanitizeRitualGate(value: unknown): Record<string, unknown> | undefined {
  if (!isRecord(value)) return undefined;

  const requiredContexts = normalizeStringArray(value.requiredContexts).filter((context) =>
    KNOWN_CONTEXT_SET.has(context),
  );
  const acceptedTokens = normalizeStringArray(value.acceptedTokens);
  const rejectionMessage = normalizeString(value.rejectionMessage);
  const enabled = normalizeBoolean(value.enabled);
  const requireWhenVowMode = normalizeBoolean(value.requireWhenVowMode);

  return {
    ...(enabled !== undefined ? { enabled } : {}),
    ...(requiredContexts.length > 0 ? { requiredContexts } : {}),
    ...(acceptedTokens.length > 0 ? { acceptedTokens } : {}),
    ...(requireWhenVowMode !== undefined ? { requireWhenVowMode } : {}),
    ...(rejectionMessage ? { rejectionMessage } : {}),
  };
}

function convertLegacySigil(parsed: Record<string, unknown>): ProjectSigil {
  const legacyResponseShape = isRecord(parsed.responseShape) ? parsed.responseShape : {};
  const legacyVeilMode = isRecord(parsed.veilMode) ? parsed.veilMode : {};
  const legacyInvocationGate = isRecord(parsed.invocationGate) ? parsed.invocationGate : {};
  const legacyRitualGate = sanitizeRitualGate(parsed.ritualGate);
  const acceptPattern = normalizeString(parsed.acceptPattern);
  const invocationAcceptList = normalizeStringArray(legacyInvocationGate.accept);
  const denyIfUnsealed =
    normalizeBoolean(legacyInvocationGate.denyIfUnsealed) ??
    (parsed.denyIfUnsealed === true);
  const traceThreshold = clamp(
    normalizeNumber(legacyInvocationGate.threshold) ??
      normalizeNumber(parsed.traceThreshold) ??
      DEFAULT_PROJECT_SIGIL.invocationGate.threshold,
    0,
    1,
  );
  const responseDefaultPrompt =
    normalizeString(legacyResponseShape.defaultPrompt) || normalizeString(parsed.entryVow);
  const responseMaxOutputTokens = normalizeNumber(legacyResponseShape.maxOutputTokens);
  const responseMaxOutputChars =
    normalizeNumber(legacyResponseShape.maxOutputChars) ??
    normalizeNumber(legacyResponseShape.maxResponseLength);
  const responseVeilBehaviorToken = normalizeString(legacyResponseShape.veilBehavior).toLowerCase();
  const responseVeilBehavior =
    responseVeilBehaviorToken === "strict" ||
    responseVeilBehaviorToken === "audit-only" ||
    responseVeilBehaviorToken === "off"
      ? responseVeilBehaviorToken
      : undefined;
  const seal = normalizeString(parsed.seal);
  const entryVow = normalizeString(parsed.entryVow);
  const invocationGateEnabled =
    normalizeBoolean(legacyInvocationGate.enabled) ??
    (legacyVeilMode.enabled === true || denyIfUnsealed || Boolean(acceptPattern));
  const invocationGateMode = normalizeString(legacyInvocationGate.mode);
  const acceptPatterns =
    invocationAcceptList.length > 0
      ? invocationAcceptList
      : acceptPattern
        ? [acceptPattern]
        : DEFAULT_PROJECT_SIGIL.invocationGate.accept;
  const memorySeal =
    normalizeString(legacyInvocationGate.memorySeal) ||
    seal ||
    DEFAULT_PROJECT_SIGIL.invocationGate.memorySeal;
  const invocationGateVeil =
    normalizeBoolean(legacyInvocationGate.veil) ??
    (typeof legacyVeilMode.enabled === "boolean"
      ? legacyVeilMode.enabled
      : DEFAULT_PROJECT_SIGIL.invocationGate.veil);
  const requireTraceSeal =
    normalizeBoolean(legacyInvocationGate.requireTraceSeal) ?? denyIfUnsealed;
  const rejectionMessage =
    normalizeString(legacyInvocationGate.rejectionMessage) ||
    normalizeString(parsed.rejectPattern) ||
    undefined;
  const projectName =
    normalizeString(parsed.projectName) ||
    normalizeString(parsed.name) ||
    DEFAULT_PROJECT_SIGIL.projectName;
  const resonanceTags = normalizeStringArray(parsed.resonanceTags);
  const symbolicTraits = sanitizeSymbolicTraits(parsed.symbolicTraits);
  const contextProfiles = sanitizeContextProfiles(parsed.contextProfiles);

  return projectSigilSchema.parse({
    version: 1,
    projectName,
    seal: seal || memorySeal,
    ...(entryVow ? { entryVow } : {}),
    ...(resonanceTags.length > 0 ? { resonanceTags } : {}),
    ...(symbolicTraits.length > 0 ? { symbolicTraits } : {}),
    ...(Object.keys(contextProfiles).length > 0 ? { contextProfiles } : {}),
    allowedModels: normalizeStringArray(parsed.allowedModels),
    ...(legacyRitualGate ? { ritualGate: legacyRitualGate } : {}),
    invocationGate: {
      enabled: invocationGateEnabled,
      threshold: traceThreshold,
      accept: acceptPatterns,
      mode: invocationGateMode === "direct" ? "direct" : "whisper",
      memorySeal,
      veil: invocationGateVeil,
      denyIfUnsealed,
      requireTraceSeal,
      rejectionMessage,
    },
    responseShape: {
      tone: normalizeString(legacyResponseShape.tone) || DEFAULT_PROJECT_SIGIL.responseShape.tone,
      style:
        normalizeString(legacyResponseShape.style) || DEFAULT_PROJECT_SIGIL.responseShape.style,
      ...(responseMaxOutputTokens !== undefined
        ? { maxOutputTokens: Math.floor(clamp(responseMaxOutputTokens, 32, 4096)) }
        : {}),
      ...(responseMaxOutputChars !== undefined
        ? { maxOutputChars: Math.floor(clamp(responseMaxOutputChars, 120, 8000)) }
        : {}),
      ...(responseVeilBehavior ? { veilBehavior: responseVeilBehavior } : {}),
      defaultPrompt: responseDefaultPrompt || undefined,
      ...(isRecord(legacyResponseShape.attunementPolicy)
        ? { attunementPolicy: legacyResponseShape.attunementPolicy }
        : {}),
    },
  });
}

function readProjectSigilFromDisk(): ProjectSigil {
  if (!existsSync(PROJECT_SIGIL_PATH)) {
    return DEFAULT_PROJECT_SIGIL;
  }

  try {
    const raw = readFileSync(PROJECT_SIGIL_PATH, "utf-8");
    const parsed: unknown = JSON.parse(raw);

    if (isLikelyLegacySigil(parsed)) {
      return convertLegacySigil(parsed);
    }

    if (!isRecord(parsed)) {
      return projectSigilSchema.parse(parsed);
    }

    try {
      return projectSigilSchema.parse(parsed);
    } catch {
      return convertLegacySigil(parsed);
    }
  } catch (error) {
    console.error(
      `Failed to parse .sigil.json, falling back to defaults: ${errorToLogString(error)}`,
    );
    return DEFAULT_PROJECT_SIGIL;
  }
}

let cachedProjectSigil: ProjectSigil = readProjectSigilFromDisk();

export function getProjectSigil(): ProjectSigil {
  return cachedProjectSigil;
}

export function refreshProjectSigil(): ProjectSigil {
  cachedProjectSigil = readProjectSigilFromDisk();
  return cachedProjectSigil;
}

export function writeProjectSigil(next: ProjectSigil): ProjectSigil {
  const validated = projectSigilSchema.parse(next);
  writeFileSync(PROJECT_SIGIL_PATH, JSON.stringify(validated, null, 2), "utf-8");
  cachedProjectSigil = validated;
  return validated;
}

function scheduleSigilReload(): void {
  if (pendingReloadTimer) {
    clearTimeout(pendingReloadTimer);
  }

  pendingReloadTimer = setTimeout(() => {
    pendingReloadTimer = null;
    cachedProjectSigil = readProjectSigilFromDisk();
  }, 80);
}

export function startProjectSigilWatcher(): void {
  if (sigilWatcher) return;

  try {
    sigilWatcher = watch(process.cwd(), { persistent: false }, (_eventType, filename) => {
      if (!filename) return;
      if (path.basename(filename.toString()) !== PROJECT_SIGIL_FILENAME) return;
      scheduleSigilReload();
    });

    sigilWatcher.on("error", (error) => {
      console.error(`Project sigil watcher error: ${errorToLogString(error)}`);
    });
  } catch (error) {
    console.error(`Failed to start project sigil watcher: ${errorToLogString(error)}`);
  }
}
