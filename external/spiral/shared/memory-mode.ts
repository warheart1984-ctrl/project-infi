export const memoryModeValues = ["open", "sigil-bound", "sealed"] as const;

export type MemoryMode = (typeof memoryModeValues)[number];

const memoryModeCycle: MemoryMode[] = ["open", "sigil-bound", "sealed"];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function normalize(value: unknown): string {
  return typeof value === "string" ? value.trim().toLowerCase() : "";
}

function asBoolean(value: unknown): boolean | undefined {
  return typeof value === "boolean" ? value : undefined;
}

export function isMemoryMode(value: unknown): value is MemoryMode {
  const normalized = normalize(value);
  return normalized === "open" || normalized === "sigil-bound" || normalized === "sealed";
}

export function normalizeMemoryMode(value: unknown, fallback: MemoryMode = "sigil-bound"): MemoryMode {
  const normalized = normalize(value);
  if (normalized === "open" || normalized === "sigil-bound" || normalized === "sealed") {
    return normalized;
  }
  return fallback;
}

export function resolveMemoryModeFromProviderSettings(
  settings: unknown,
  fallback: MemoryMode = "sigil-bound",
): MemoryMode {
  if (!isRecord(settings)) return fallback;

  const configuredMode = settings.memoryMode;
  if (isMemoryMode(configuredMode)) {
    return configuredMode;
  }

  const temporaryChatEnabled = asBoolean(settings.temporaryChatEnabled);
  if (temporaryChatEnabled === true) {
    return "sealed";
  }

  const memoryEnabled = asBoolean(settings.memoryEnabled);
  if (memoryEnabled === false) {
    return "sealed";
  }

  const historyReferenceEnabled = asBoolean(settings.historyReferenceEnabled);
  if (historyReferenceEnabled === false) {
    return "sigil-bound";
  }

  return fallback;
}

export function nextMemoryMode(current: MemoryMode): MemoryMode {
  const index = memoryModeCycle.indexOf(current);
  if (index === -1) return memoryModeCycle[0];
  return memoryModeCycle[(index + 1) % memoryModeCycle.length];
}
